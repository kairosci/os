from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from typing import TypedDict

import yaml


class ExitCodes(TypedDict):
  usage: int
  invalid_name: int
  incomplete: int
  operation_failed: int


class DoneConfig(TypedDict):
  default_language: str
  directory: str
  mode: str
  exact_arguments: int
  actions: list[str]
  check_action: str
  mark_action: str
  ensure_action: str
  invalid_names: list[str]
  exit_codes: ExitCodes
  messages: dict[str, dict[str, str]]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid done configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid done configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid done configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid done configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _config() -> DoneConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/done.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  arguments = _mapping(config.get("argument_counts"), "argument_counts")
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
    "exact_arguments": _integer(arguments.get("exact"), "argument_counts.exact"),
    "actions": _text_list(config.get("actions"), "actions"),
    "check_action": _text(action_map.get("check"), "actions_map.check"),
    "mark_action": _text(action_map.get("mark"), "actions_map.mark"),
    "ensure_action": _text(action_map.get("ensure"), "actions_map.ensure"),
    "invalid_names": _text_list(config.get("invalid_names"), "invalid_names"),
    "exit_codes": {
      "usage": _integer(codes.get("usage"), "exit_codes.usage"),
      "invalid_name": _integer(codes.get("invalid_name"), "exit_codes.invalid_name"),
      "incomplete": _integer(codes.get("incomplete"), "exit_codes.incomplete"),
      "operation_failed": _integer(codes.get("operation_failed"), "exit_codes.operation_failed"),
    },
    "messages": messages,
  }


def _message(config: DoneConfig, key: str, **values: str) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  translations = config["messages"]
  selected_language = language if language in translations else config["default_language"]
  return translations[selected_language][key].format(**values)


def _open_directory(config: DoneConfig, create: bool) -> int | None:
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


def _mark(directory_fd: int, name: str, config: DoneConfig, exclusive: bool) -> bool:
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
  try:
    config = _config()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load done configuration: {error}", file=sys.stderr)
    return 1
  if len(sys.argv) != config["exact_arguments"]:
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
    directory_fd = _open_directory(config, action != config["check_action"])
    if directory_fd is None:
      return config["exit_codes"]["incomplete"]
    if action == config["check_action"]:
      return 0 if _check(directory_fd, name) else config["exit_codes"]["incomplete"]
    created = _mark(directory_fd, name, config, action == config["ensure_action"])
    return 0 if created else config["exit_codes"]["incomplete"]
  except OSError as error:
    print(_message(config, "operation_failed", path=str(error)), file=sys.stderr)
    return config["exit_codes"]["operation_failed"]
  finally:
    if directory_fd is not None:
      os.close(directory_fd)
