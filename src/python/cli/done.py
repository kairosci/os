from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import yaml


def _config() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/done.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid done configuration")
  return config


def _message(config: dict, key: str, **values: str) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  translations = config["messages"]
  language = language if language in translations else config["default_language"]
  return translations[language][key].format(**values)


def _open_directory(config: dict, create: bool) -> int | None:
  directory = Path.home() / config["directory"]
  if directory.is_symlink():
    raise NotADirectoryError(directory)
  if not directory.exists():
    if not create:
      return None
    directory.mkdir(parents=True, exist_ok=True)
  if directory.is_symlink() or not directory.is_dir():
    raise NotADirectoryError(directory)
  flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
  return os.open(directory, flags)


def _mark(directory_fd: int, name: str, config: dict, exclusive: bool) -> bool:
  flags = os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
  if exclusive:
    flags |= os.O_EXCL
  try:
    descriptor = os.open(name, flags, int(config["mode"], 8), dir_fd=directory_fd)
  except FileExistsError:
    if exclusive:
      return False
    raise
  try:
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
      raise OSError("marker is not a regular file")
  finally:
    os.close(descriptor)
  if not exclusive:
    os.utime(name, None, dir_fd=directory_fd, follow_symlinks=False)
  return True


def _check(directory_fd: int, name: str) -> bool:
  flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
  try:
    descriptor = os.open(name, flags, dir_fd=directory_fd)
  except OSError:
    return False
  try:
    return stat.S_ISREG(os.fstat(descriptor).st_mode)
  finally:
    os.close(descriptor)


def main() -> int:
  config = _config()
  if len(sys.argv) != config["argument_counts"]["exact"]:
    print(_message(config, "usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]

  action, name = sys.argv[1:]
  if action not in config["actions"]:
    print(_message(config, "usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]
  if not name or "/" in name or name in config["invalid_names"]:
    print(_message(config, "invalid_name", name=name), file=sys.stderr)
    return config["exit_codes"]["invalid_name"]

  directory_fd = None
  try:
    directory_fd = _open_directory(config, action != config["actions_map"]["check"])
    if directory_fd is None:
      return config["exit_codes"]["incomplete"]
    if action == config["actions_map"]["check"]:
      return 0 if _check(directory_fd, name) else config["exit_codes"]["incomplete"]
    created = _mark(directory_fd, name, config, action == config["actions_map"]["ensure"])
    return 0 if created else config["exit_codes"]["incomplete"]
  except OSError as error:
    print(_message(config, "operation_failed", path=error), file=sys.stderr)
    return config["exit_codes"]["operation_failed"]
  finally:
    if directory_fd is not None:
      os.close(directory_fd)
