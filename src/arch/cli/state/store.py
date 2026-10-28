from __future__ import annotations

import fnmatch
import os
import stat
import sys
from pathlib import Path
from typing import TypedDict

import yaml


class ExitCodes(TypedDict):
  usage: int
  invalid_name: int
  operation_failed: int


class StateConfig(TypedDict):
  default_language: str
  directory: str
  mode: str
  minimum_arguments: int
  actions: list[str]
  set_action: str
  clear_action: str
  invalid_names: list[str]
  exit_codes: ExitCodes
  messages: dict[str, dict[str, str]]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid state configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid state configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid state configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid state configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _config() -> StateConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/state.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  action_map = _mapping(config.get("actions_map"), "actions_map")
  codes = _mapping(config.get("exit_codes"), "exit_codes")
  raw_messages = _mapping(config.get("messages"), "messages")
  messages: dict[str, dict[str, str]] = {}
  for language, raw_table in raw_messages.items():
    locale = _text(language, "messages language")
    table = _mapping(raw_table, f"messages.{locale}")
    messages[locale] = {
      _text(key, f"messages.{locale} key"): _text(value, f"messages.{locale} value")
      for key, value in table.items()
    }
  return {
    "default_language": _text(config.get("default_language"), "default_language"),
    "directory": _text(config.get("directory"), "directory"),
    "mode": _text(config.get("mode"), "mode"),
    "minimum_arguments": _integer(
      _mapping(config.get("argument_counts"), "argument_counts").get("minimum"),
      "argument_counts.minimum",
    ),
    "actions": _text_list(config.get("actions"), "actions"),
    "set_action": _text(action_map.get("set"), "actions_map.set"),
    "clear_action": _text(action_map.get("clear"), "actions_map.clear"),
    "invalid_names": _text_list(config.get("invalid_names"), "invalid_names"),
    "exit_codes": {
      "usage": _integer(codes.get("usage"), "exit_codes.usage"),
      "invalid_name": _integer(codes.get("invalid_name"), "exit_codes.invalid_name"),
      "operation_failed": _integer(codes.get("operation_failed"), "exit_codes.operation_failed"),
    },
    "messages": messages,
  }


def _message(config: StateConfig, key: str, **values: str) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  translations = config["messages"]
  selected_language = language if language in translations else config["default_language"]
  return translations[selected_language][key].format(**values)


def _open_state_directory(config: StateConfig) -> int:
  directory = Path.home() / config["directory"]
  directory.mkdir(parents=True, exist_ok=True)
  if directory.is_symlink() or not directory.is_dir():
    raise NotADirectoryError(directory)
  flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
  return os.open(directory, flags)


def _set(directory_fd: int, name: str, config: StateConfig) -> None:
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
  try:
    config = _config()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load state configuration: {error}", file=sys.stderr)
    return 1
  if len(sys.argv) < config["minimum_arguments"]:
    print(_message(config, "usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]

  action, name = sys.argv[1:3]
  if action not in config["actions"]:
    print(_message(config, "unknown_action", action=action), file=sys.stderr)
    return config["exit_codes"]["usage"]
  if not name:
    print(_message(config, "usage_action", action=action), file=sys.stderr)
    return config["exit_codes"]["usage"]
  if action == config["set_action"] and (
    "/" in name or name in config["invalid_names"]
  ):
    print(_message(config, "invalid_name", name=name), file=sys.stderr)
    return config["exit_codes"]["invalid_name"]

  directory_fd = -1
  try:
    directory_fd = _open_state_directory(config)
    if action == config["set_action"]:
      _set(directory_fd, name, config)
    else:
      _clear(directory_fd, name)
  except OSError as error:
    print(_message(config, "operation_failed", path=str(error)), file=sys.stderr)
    return config["exit_codes"]["operation_failed"]
  finally:
    if directory_fd >= 0:
      os.close(directory_fd)
  return 0
