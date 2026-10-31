from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Paths(TypedDict):
  config_home_environment: str
  home_environment: str
  default_config_home: str
  config_relative: str
  encoding: str


class Limits(TypedDict):
  arguments: int
  backend_characters: int


class Commands(TypedDict):
  installer_missing: list[str]
  launch_installer: list[str]


class Messages(TypedDict):
  usage: str
  no_backend: str
  invalid_backend: str
  installer_missing: str
  config_error: str
  command_error: str


class Statuses(TypedDict):
  success: int
  invalid_arguments: int
  invalid_backend: int
  no_backend: int
  installer_missing: int
  config_error: int
  command_error: int


class Settings(TypedDict):
  paths: Paths
  limits: Limits
  backend_pattern: str
  commands: Commands
  messages: Messages
  statuses: Statuses


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError()
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError()
  return value


def _integer(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError()
  return value


def _strings(value: object) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError()
  return cast(list[str], value)


def _settings() -> Settings:
  document = _mapping(yaml.safe_load((Path(os.environ["AP"]) / "data/cli/default-dictation.yml").read_text(encoding="utf-8")))
  paths = _mapping(document.get("paths"))
  limits = _mapping(document.get("limits"))
  patterns = _mapping(document.get("patterns"))
  commands = _mapping(document.get("commands"))
  messages = _mapping(document.get("messages"))
  statuses = _mapping(document.get("statuses"))
  pattern = _text(patterns.get("backend"))
  re.compile(pattern)
  return {
    "paths": {
      "config_home_environment": _text(paths.get("config_home_environment")),
      "home_environment": _text(paths.get("home_environment")),
      "default_config_home": _text(paths.get("default_config_home")),
      "config_relative": _text(paths.get("config_relative")),
      "encoding": _text(paths.get("encoding")),
    },
    "limits": {
      "arguments": _integer(limits.get("arguments")),
      "backend_characters": _integer(limits.get("backend_characters")),
    },
    "backend_pattern": pattern,
    "commands": {
      "installer_missing": _strings(commands.get("installer_missing")),
      "launch_installer": _strings(commands.get("launch_installer")),
    },
    "messages": {
      "usage": _text(messages.get("usage")),
      "no_backend": _text(messages.get("no_backend")),
      "invalid_backend": _text(messages.get("invalid_backend")),
      "installer_missing": _text(messages.get("installer_missing")),
      "config_error": _text(messages.get("config_error")),
      "command_error": _text(messages.get("command_error")),
    },
    "statuses": {
      "success": _integer(statuses.get("success")),
      "invalid_arguments": _integer(statuses.get("invalid_arguments")),
      "invalid_backend": _integer(statuses.get("invalid_backend")),
      "no_backend": _integer(statuses.get("no_backend")),
      "installer_missing": _integer(statuses.get("installer_missing")),
      "config_error": _integer(statuses.get("config_error")),
      "command_error": _integer(statuses.get("command_error")),
    },
  }


def _config_path(settings: Settings) -> Path:
  paths = settings["paths"]
  config_home = os.environ.get(paths["config_home_environment"])
  if config_home is None or config_home == "":
    home = os.environ[paths["home_environment"]]
    relative_home = Path(paths["default_config_home"])
    if relative_home.is_absolute() or ".." in relative_home.parts:
      raise ValueError()
    root = Path(home).joinpath(*relative_home.parts)
  else:
    root = Path(config_home)
  relative_config = Path(paths["config_relative"])
  if relative_config.is_absolute() or ".." in relative_config.parts:
    raise ValueError()
  return root.joinpath(*relative_config.parts)


def _read_backend(path: Path, settings: Settings) -> str:
  try:
    with path.open(encoding=settings["paths"]["encoding"]) as stream:
      backend = stream.readline(settings["limits"]["backend_characters"] + 1).rstrip("\n")
  except FileNotFoundError:
    return ""
  if len(backend) > settings["limits"]["backend_characters"]:
    return "\x00"
  return backend


def _valid_backend(backend: str, settings: Settings) -> bool:
  return re.fullmatch(settings["backend_pattern"], backend) is not None


def default_dictation_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, UnicodeError, ValueError, yaml.YAMLError, re.error):
    print("Could not load dictation command settings.", file=sys.stderr)
    return 1

  if len(arguments) > settings["limits"]["arguments"]:
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]

  try:
    backend = arguments[0] if arguments else _read_backend(_config_path(settings), settings)
  except (KeyError, OSError, UnicodeError, ValueError):
    print(settings["messages"]["config_error"], file=sys.stderr)
    return settings["statuses"]["config_error"]

  if not backend:
    print(settings["messages"]["no_backend"], file=sys.stderr)
    return settings["statuses"]["no_backend"]
  if not _valid_backend(backend, settings):
    print(settings["messages"]["invalid_backend"], file=sys.stderr)
    return settings["statuses"]["invalid_backend"]
  if not arguments:
    print(backend)
    return settings["statuses"]["success"]

  installer = f"arch-install-dictation-{backend}"
  try:
    missing = subprocess.run([*settings["commands"]["installer_missing"], installer], check=False)
  except OSError:
    print(settings["messages"]["command_error"], file=sys.stderr)
    return settings["statuses"]["command_error"]
  if missing.returncode == settings["statuses"]["success"]:
    print(settings["messages"]["installer_missing"], file=sys.stderr)
    return settings["statuses"]["installer_missing"]

  try:
    return subprocess.run([*settings["commands"]["launch_installer"], installer], check=False).returncode
  except OSError:
    print(settings["messages"]["command_error"], file=sys.stderr)
    return settings["statuses"]["command_error"]
