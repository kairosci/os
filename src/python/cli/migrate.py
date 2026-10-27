from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/migrate.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError
  return config


def localized(config: dict[str, Any], name: str, *arguments: str) -> str:
  key = config["messages"][name]
  arch_path = os.environ["ARCH_PATH"]
  i18n_command = [part.format(arch_path=arch_path) for part in config["commands"]["i18n"]]
  result = subprocess.run(
    [*i18n_command, key, *arguments],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def parse_arguments(config: dict[str, Any], arguments: list[str]) -> str | None:
  mode = config["modes"]["run"]
  for argument in arguments:
    if argument in config["arguments"]["pending"]:
      mode = config["modes"]["pending"]
    elif argument in config["arguments"]["help"]:
      print(localized(config, "usage"))
      return config["statuses"]["success"]
    else:
      print(localized(config, "unknown_option", argument), file=sys.stderr)
      print(localized(config, "usage"), file=sys.stderr)
      return config["statuses"]["failure"]
  return mode


def migration_files(config: dict[str, Any], directory: Path) -> list[Path]:
  if not directory.is_dir():
    return []
  settings = config["migrations"]
  suffixes = set(settings["suffixes"])
  return sorted(
    (
      path for path in directory.iterdir()
      if path.suffix in suffixes
      and path.is_file()
      and (settings["include_hidden"] or not path.name.startswith("."))
    ),
    key=lambda path: path.name,
  )


def marker_for(config: dict[str, Any], name: str, state_dir: Path, home: Path) -> Path:
  migration = Path(name)
  suffixes = config["migrations"]["suffixes"]
  marker_names = [
    name,
    *(migration.with_suffix(suffix).name for suffix in suffixes if suffix != migration.suffix),
  ]
  directories = [state_dir]
  for entry in config["state"]["legacy_directories"]:
    directories.append(Path(
      os.environ.get(entry["environment"]) or str(home / entry["directory"])
    ))
  for directory in directories:
    for marker_name in marker_names:
      marker = directory / marker_name
      if marker.is_file():
        return marker
  return state_dir / name


def pending_migrations(
  config: dict[str, Any], files: list[Path], state_dir: Path, home: Path
) -> list[Path]:
  return [
    path for path in files
    if not marker_for(config, path.name, state_dir, home).is_file()
  ]


def wait_for_pacman(config: dict[str, Any]) -> bool:
  lock = Path(config["pacman"]["lock_file"])
  if not lock.exists():
    return True
  print(localized(config, "waiting"))
  for _ in range(int(config["pacman"]["wait_attempts"])):
    if not lock.exists():
      return True
    time.sleep(float(config["pacman"]["wait_interval_seconds"]))
  if not lock.exists():
    return True
  print(localized(config, "lock_timeout"))
  return False


def run_migration(config: dict[str, Any], path: Path, root: Path) -> int:
  if path.suffix == config["migrations"]["python_suffix"]:
    command = [*config["commands"]["python"], str(path)]
  else:
    command = [*config["commands"]["shell"], str(path)]
  environment = os.environ.copy()
  environment["ARCH_PATH"] = str(root)
  result = subprocess.run(command, env=environment, check=False)
  return result.returncode


def main(arguments: list[str] | None = None) -> int:
  config: dict[str, Any] | None = None
  try:
    config = load_config()
    mode = parse_arguments(config, sys.argv[1:] if arguments is None else arguments)
    if not isinstance(mode, str):
      return int(mode)

    root = Path(os.environ["ARCH_PATH"])
    home = Path.home()
    state = config["state"]
    state_dir = Path(os.environ.get(state["environment"]) or str(home / state["directory"]))
    migration_dir = root / config["migrations"]["directory"]
    files = migration_files(config, migration_dir)

    if mode == config["modes"]["pending"]:
      pending = pending_migrations(config, files, state_dir, home)
      if not pending:
        return int(config["statuses"]["no_pending"])
      for path in pending:
        print(path.name)
      return int(config["statuses"]["success"])

    if not wait_for_pacman(config):
      return int(config["statuses"]["lock_timeout"])

    state_dir.mkdir(parents=True, exist_ok=True)
    for path in files:
      marker = marker_for(config, path.name, state_dir, home)
      if marker.is_file():
        continue
      print(localized(config, "running", path.stem))
      result = run_migration(config, path, root)
      if result == int(config["statuses"]["deferred"]):
        print(localized(config, "deferred", path.name))
        continue
      if result != int(config["statuses"]["success"]):
        return result
      marker.parent.mkdir(parents=True, exist_ok=True)
      marker.touch()

    try:
      subprocess.run(
        [*config["commands"]["dismiss"], config["notifications"]["migration_title"]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
      )
    except OSError:
      pass
    return int(config["statuses"]["success"])
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    if config is not None:
      print(localized(config, "failed"), file=sys.stderr)
      return int(config["statuses"]["failure"])
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
