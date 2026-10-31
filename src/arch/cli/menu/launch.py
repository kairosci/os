from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Statuses(TypedDict):
  configuration_error: int
  timeout: int
  command_error: int
  signal_status_base: int


class Messages(TypedDict):
  timeout: str
  command_error: str


class Settings(TypedDict):
  commands: dict[str, list[str]]
  timeout_seconds: int
  statuses: Statuses
  messages: Messages


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"{label} must be non-empty text")
  return value


def _status(value: object, label: str, *, zero_allowed: bool = False) -> int:
  if type(value) is not int or value < (0 if zero_allowed else 1) or value > 255:
    raise ValueError(f"{label} must be an exit status")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/menu-launch.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "configuration")
  raw_commands = _mapping(document.get("commands"), "commands")
  commands: dict[str, list[str]] = {}
  for name, command in raw_commands.items():
    if not name.startswith("arch-menu-") or not isinstance(command, list) or not command or not all(
      isinstance(argument, str) and argument for argument in command
    ):
      raise ValueError("commands must map menu entrypoints to non-empty argv lists")
    commands[name] = command
  timeout = document.get("timeout_seconds")
  if type(timeout) is not int or timeout <= 0:
    raise ValueError("timeout_seconds must be a positive integer")
  raw_statuses = _mapping(document.get("statuses"), "statuses")
  signal_base = _status(raw_statuses.get("signal_status_base"), "signal_status_base", zero_allowed=True)
  if signal_base > 255:
    raise ValueError("signal_status_base must not exceed 255")
  raw_messages = _mapping(document.get("messages"), "messages")
  return {
    "commands": commands,
    "timeout_seconds": timeout,
    "statuses": {
      "configuration_error": _status(raw_statuses.get("configuration_error"), "configuration_error"),
      "timeout": _status(raw_statuses.get("timeout"), "timeout"),
      "command_error": _status(raw_statuses.get("command_error"), "command_error"),
      "signal_status_base": signal_base,
    },
    "messages": {
      "timeout": _text(raw_messages.get("timeout"), "messages.timeout"),
      "command_error": _text(raw_messages.get("command_error"), "messages.command_error"),
    },
  }


def main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  command = settings["commands"].get(Path(sys.argv[0]).name)
  if command is None:
    print("Unknown menu entrypoint", file=sys.stderr)
    return settings["statuses"]["configuration_error"]

  try:
    result = subprocess.run(command, check=False, timeout=settings["timeout_seconds"])
  except subprocess.TimeoutExpired:
    print(settings["messages"]["timeout"], file=sys.stderr)
    return settings["statuses"]["timeout"]
  except OSError as error:
    print(f"{settings['messages']['command_error']}: {error}", file=sys.stderr)
    return settings["statuses"]["command_error"]

  if result.returncode >= 0:
    return result.returncode
  return min(255, settings["statuses"]["signal_status_base"] - result.returncode)
