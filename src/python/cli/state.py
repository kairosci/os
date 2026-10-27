from __future__ import annotations

import fnmatch
import os
import stat
import sys
from pathlib import Path

import yaml


def _config() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/state.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid state configuration")
  return config


def _message(config: dict, key: str, **values: str) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  translations = config["messages"]
  language = language if language in translations else config["default_language"]
  return translations[language][key].format(**values)


def _open_state_directory(config: dict) -> int:
  directory = Path.home() / config["directory"]
  directory.mkdir(parents=True, exist_ok=True)
  if directory.is_symlink() or not directory.is_dir():
    raise NotADirectoryError(directory)
  flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
  return os.open(directory, flags)


def _set(directory_fd: int, name: str, config: dict) -> None:
  flags = os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
  descriptor = os.open(name, flags, int(config["mode"], 8), dir_fd=directory_fd)
  try:
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
      raise OSError("state path is not a regular file")
  finally:
    os.close(descriptor)
  os.utime(name, None, dir_fd=directory_fd, follow_symlinks=False)


def _clear(directory_fd: int, pattern: str) -> None:
  with os.scandir(directory_fd) as entries:
    names = [
      entry.name
      for entry in entries
      if fnmatch.fnmatchcase(entry.name, pattern) and entry.is_file(follow_symlinks=False)
    ]
  for name in names:
    os.unlink(name, dir_fd=directory_fd)


def main() -> int:
  config = _config()
  if len(sys.argv) < config["argument_counts"]["minimum"]:
    print(_message(config, "usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]

  action, name = sys.argv[1:3]
  if action not in config["actions"]:
    print(_message(config, "unknown_action", action=action), file=sys.stderr)
    return config["exit_codes"]["usage"]
  if not name:
    print(_message(config, "usage_action", action=action), file=sys.stderr)
    return config["exit_codes"]["usage"]
  if action == config["actions_map"]["set"] and (
    "/" in name or name in config["invalid_names"]
  ):
    print(_message(config, "invalid_name", name=name), file=sys.stderr)
    return config["exit_codes"]["invalid_name"]

  directory_fd = -1
  try:
    directory_fd = _open_state_directory(config)
    if action == config["actions_map"]["set"]:
      _set(directory_fd, name, config)
    else:
      _clear(directory_fd, name)
  except OSError as error:
    print(_message(config, "operation_failed", path=error), file=sys.stderr)
    return config["exit_codes"]["operation_failed"]
  finally:
    if directory_fd >= 0:
      os.close(directory_fd)
  return 0
