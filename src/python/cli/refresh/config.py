"""Restore a shipped user config while preserving backups and safe links."""

from __future__ import annotations

import filecmp
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any

import yaml


def settings() -> dict[str, Any]:
  path = Path(os.environ["ARCH_PATH"]) / "data/cli/refresh-config.yml"
  return yaml.safe_load(path.read_text(encoding="utf-8"))


def localized(config: dict[str, Any], key: str, *values: str) -> str:
  result = subprocess.run(
    [*config["commands"]["localize"], config["messages"][key], *values],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def beneath(path: Path, root: Path) -> bool:
  try:
    path.relative_to(root)
    return True
  except ValueError:
    return False


def temporary_file(directory: Path, prefix: str) -> Path:
  descriptor, filename = tempfile.mkstemp(prefix=prefix, dir=directory)
  os.close(descriptor)
  return Path(filename)


def copy(config: dict[str, Any], source: Path, destination: Path) -> int:
  return subprocess.run(
    [*config["commands"]["copy"], str(source), str(destination)],
    check=False,
  ).returncode


def main(arguments: list[str] | None = None) -> int:
  config = settings()
  args = sys.argv[1:] if arguments is None else arguments
  status = config["statuses"]
  if len(args) != 1 or not args[0]:
    print(localized(config, "usage", sys.argv[0]), file=sys.stderr)
    return status["failure"]

  config_name = args[0]
  segments = config_name.split("/")
  if config_name.startswith("/") or any(segment in config["validation"]["forbidden_path_segments"] for segment in segments):
    print(localized(config, "invalid_path", config_name), file=sys.stderr)
    return status["failure"]

  try:
    arch_root = Path(os.environ["ARCH_PATH"]).resolve(strict=True)
    source_root = (arch_root / config["paths"]["source_directory"]).resolve(strict=True)
    source_candidate = source_root.joinpath(*segments)
    cursor = source_root
    for segment in segments:
      cursor /= segment
      if cursor.is_symlink():
        print(localized(config, "unsafe_path", config_name), file=sys.stderr)
        return status["failure"]
    source_file = source_candidate.resolve(strict=True)
  except FileNotFoundError:
    print(localized(config, "not_shipped", config_name), file=sys.stderr)
    return status["failure"]
  except (OSError, RuntimeError, ValueError):
    print(localized(config, "unsafe_path", config_name), file=sys.stderr)
    return status["failure"]

  if not beneath(source_file, source_root):
    print(localized(config, "unsafe_path", config_name), file=sys.stderr)
    return status["failure"]
  if not source_file.is_file():
    print(localized(config, "not_shipped", config_name), file=sys.stderr)
    return status["failure"]

  config_home = os.environ.get(config["paths"]["config_home_environment"])
  if not config_home:
    home = Path(os.environ[config["paths"]["home_environment"]])
    config_home = str(home / config["paths"]["default_config_home"])

  try:
    destination_root = Path(config_home).resolve(strict=False)
    destination_file = destination_root.joinpath(*segments).resolve(strict=False)
  except (OSError, RuntimeError, ValueError):
    print(localized(config, "invalid_path", config_name), file=sys.stderr)
    return status["failure"]

  if not beneath(destination_file, destination_root):
    print(localized(config, "unsafe_path", config_name), file=sys.stderr)
    return status["failure"]
  if destination_file.exists() and not destination_file.is_file():
    print(localized(config, "invalid_path", config_name), file=sys.stderr)
    return status["failure"]

  temporary: Path | None = None
  backup: Path | None = None
  keep_backup = False
  try:
    destination_file.parent.mkdir(parents=True, exist_ok=True)
    destination_file = destination_root.joinpath(*segments).resolve(strict=False)
    if not beneath(destination_file, destination_root):
      print(localized(config, "unsafe_path", config_name), file=sys.stderr)
      return status["failure"]
    if destination_file.exists() and not destination_file.is_file():
      print(localized(config, "invalid_path", config_name), file=sys.stderr)
      return status["failure"]

    temporary = temporary_file(destination_file.parent, config["temporary_files"]["replacement_prefix"])
    copy_status = copy(config, source_file, temporary)
    if copy_status != status["success"]:
      return copy_status

    if destination_file.is_file():
      if filecmp.cmp(temporary, destination_file, shallow=False):
        return status["success"]
      mode = stat.S_IMODE(destination_file.stat().st_mode)
      backup = temporary_file(
        destination_file.parent,
        destination_file.name + config["temporary_files"]["backup_suffix"],
      )
      copy_status = copy(config, destination_file, backup)
      if copy_status != status["success"]:
        return copy_status
    else:
      mode = stat.S_IMODE(source_file.stat().st_mode)

    os.chmod(temporary, mode)
    os.replace(temporary, destination_file)
    temporary = None
    if backup is not None:
      keep_backup = True
      message = localized(config, "replaced", str(destination_file), str(backup))
      print(f"{config['colors']['changed_start']}{message}{config['colors']['changed_end']}")
      subprocess.run(
        [*config["commands"]["diff"], str(destination_file), str(backup)],
        check=False,
      )
    return status["success"]
  except OSError:
    return status["failure"]
  finally:
    if temporary is not None:
      try:
        temporary.unlink(missing_ok=True)
      except OSError:
        pass
    if backup is not None and not keep_backup:
      try:
        backup.unlink(missing_ok=True)
      except OSError:
        pass


if __name__ == "__main__":
  raise SystemExit(main())
