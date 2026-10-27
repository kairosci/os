"""Restore a shipped user config while preserving backups and safe links."""

from __future__ import annotations

import filecmp
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
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


def open_directory(path: Path) -> int:
  flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
  descriptor = os.open("/", flags)
  try:
    for component in path.parts[1:]:
      try:
        child = os.open(component, flags, dir_fd=descriptor)
      except FileNotFoundError:
        os.mkdir(component, dir_fd=descriptor)
        child = os.open(component, flags, dir_fd=descriptor)
      os.close(descriptor)
      descriptor = child
    return descriptor
  except BaseException:
    os.close(descriptor)
    raise


def temporary_file(directory: int, prefix: str) -> str:
  flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
  for _ in range(10):
    name = f"{prefix}{secrets.token_hex(12)}"
    try:
      descriptor = os.open(name, flags, 0o600, dir_fd=directory)
    except FileExistsError:
      continue
    os.close(descriptor)
    return name
  raise FileExistsError


def copy(config: dict[str, Any], source: str | Path, destination: str | Path, directory: int) -> int:
  return subprocess.run(
    [*config["commands"]["copy"], str(source), str(destination)],
    check=False,
    pass_fds=(directory,),
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

  temporary: str | None = None
  backup: str | None = None
  keep_backup = False
  directory = -1
  try:
    destination_file = destination_root.joinpath(*segments).resolve(strict=False)
    if not beneath(destination_file, destination_root):
      print(localized(config, "unsafe_path", config_name), file=sys.stderr)
      return status["failure"]
    if destination_file.exists() and not destination_file.is_file():
      print(localized(config, "invalid_path", config_name), file=sys.stderr)
      return status["failure"]

    directory = open_directory(destination_file.parent)
    destination_name = destination_file.name
    directory_path = Path(f"/proc/self/fd/{directory}")
    destination_path = directory_path / destination_name
    temporary = temporary_file(directory, config["temporary_files"]["replacement_prefix"])
    temporary_path = directory_path / temporary
    copy_status = copy(config, source_file, temporary_path, directory)
    if copy_status != status["success"]:
      return copy_status

    try:
      destination_info = os.stat(destination_name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
      destination_info = None
    if destination_info is not None and not stat.S_ISREG(destination_info.st_mode):
      print(localized(config, "invalid_path", config_name), file=sys.stderr)
      return status["failure"]

    if destination_info is not None:
      if filecmp.cmp(temporary_path, destination_path, shallow=False):
        return status["success"]
      mode = stat.S_IMODE(destination_info.st_mode)
      backup = temporary_file(
        directory,
        destination_file.name + config["temporary_files"]["backup_suffix"],
      )
      copy_status = copy(config, destination_path, directory_path / backup, directory)
      if copy_status != status["success"]:
        return copy_status
    else:
      mode = stat.S_IMODE(source_file.stat().st_mode)

    descriptor = os.open(temporary, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
    try:
      os.fchmod(descriptor, mode)
      os.fsync(descriptor)
    finally:
      os.close(descriptor)
    os.replace(temporary, destination_name, src_dir_fd=directory, dst_dir_fd=directory)
    temporary = None
    os.fsync(directory)
    if backup is not None:
      keep_backup = True
      message = localized(config, "replaced", str(destination_file), str(destination_file.parent / backup))
      print(f"{config['colors']['changed_start']}{message}{config['colors']['changed_end']}")
      subprocess.run(
        [*config["commands"]["diff"], str(destination_path), str(directory_path / backup)],
        check=False,
        pass_fds=(directory,),
      )
    return status["success"]
  except OSError:
    return status["failure"]
  finally:
    if temporary is not None:
      try:
        os.unlink(temporary, dir_fd=directory)
      except OSError:
        pass
    if backup is not None and not keep_backup:
      try:
        os.unlink(backup, dir_fd=directory)
      except OSError:
        pass
    if directory >= 0:
      os.close(directory)


if __name__ == "__main__":
  raise SystemExit(main())
