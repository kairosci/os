from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/migration-dev.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError
  return config


def localized(config: dict[str, Any], name: str, *arguments: str) -> str:
  arch_path = os.environ["ARCH_PATH"]
  i18n_command = [part.format(arch_path=arch_path) for part in config["commands"]["i18n"]]
  result = subprocess.run(
    [*i18n_command, config["messages"][name], *arguments],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def main(arguments: list[str] | None = None) -> int:
  config: dict[str, Any] | None = None
  try:
    config = load_config()
    args = sys.argv[1:] if arguments is None else arguments
    no_edit = False
    deprecated_scope = False
    for argument in args:
      if argument == config["arguments"]["no_edit"]:
        no_edit = True
      elif argument in config["arguments"]["help"]:
        print(localized(config, "usage"))
        return int(config["statuses"]["success"])
      elif argument in config["arguments"]["deprecated_scopes"]:
        deprecated_scope = True
      else:
        print(localized(config, "unknown_option", argument), file=sys.stderr)
        print(localized(config, "usage"), file=sys.stderr)
        return int(config["statuses"]["failure"])

    if deprecated_scope:
      print(localized(config, "deprecated_scope"), file=sys.stderr)

    root = Path(os.environ["ARCH_PATH"])
    timestamp_result = subprocess.run(
      config["commands"]["timestamp"],
      cwd=root,
      check=False,
      capture_output=True,
      text=True,
    )
    timestamp = timestamp_result.stdout.strip()
    if timestamp_result.returncode or not timestamp.isdecimal():
      print(localized(config, "timestamp_failed"), file=sys.stderr)
      return int(config["statuses"]["failure"])

    creation = config["creation"]
    directory = root / creation["directory"]
    companion_directory = root / creation["companion_directory"]
    directory.mkdir(parents=True, exist_ok=True)
    companion_directory.mkdir(parents=True, exist_ok=True)
    resolved_root = root.resolve(strict=True)
    if any(
      not output_directory.resolve(strict=True).is_relative_to(resolved_root)
      for output_directory in (directory, companion_directory)
    ):
      raise ValueError
    step = int(creation["collision_increment"])
    if step <= 0:
      raise ValueError
    while True:
      filename = creation["filename_format"].format(timestamp=timestamp)
      path = directory / filename
      companion = companion_directory / creation["companion_filename_format"].format(
        timestamp=timestamp
      )
      if (
        path.parent != directory
        or path.suffix != creation["python_suffix"]
        or companion.parent != companion_directory
        or companion.suffix != creation["companion_suffix"]
      ):
        raise ValueError
      created: list[Path] = []
      try:
        outputs = (
          (path, creation["template"], creation["mode"]),
          (
            companion,
            yaml.safe_dump(creation["companion_template"], allow_unicode=True, sort_keys=False),
            creation["companion_mode"],
          ),
        )
        for target, content, mode in outputs:
          descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, int(mode, 8))
          created.append(target)
          os.fchmod(descriptor, int(mode, 8))
          with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        break
      except FileExistsError:
        for target in created:
          target.unlink(missing_ok=True)
        timestamp = str(int(timestamp) + step)
      except OSError:
        for target in created:
          target.unlink(missing_ok=True)
        raise

    if not no_edit:
      result = subprocess.run([*config["commands"]["editor"], str(path)], check=False)
      if result.returncode:
        return result.returncode

    print(localized(config, "created", str(path)))
    return int(config["statuses"]["success"])
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    if config is not None:
      print(localized(config, "creation_failed"), file=sys.stderr)
      return int(config["statuses"]["failure"])
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
