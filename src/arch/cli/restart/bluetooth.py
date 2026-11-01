from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  commands: list[list[str]]
  timeout: int
  unblocking_message: str
  usage_message: str
  configuration_error: str
  operation_error: str
  success: int
  invalid_arguments: int
  operation_failed: int


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError("Bluetooth restart settings must be mappings")
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError("Bluetooth restart messages must be non-empty strings")
  return value


def _status(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise TypeError("Bluetooth restart status values must be non-negative integers")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/restart-bluetooth.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  limits = _mapping(document.get("limits"))
  messages = _mapping(document.get("messages"))
  statuses = _mapping(document.get("statuses"))
  commands_value = document.get("commands")
  timeout = limits.get("command_timeout_seconds")
  if not isinstance(commands_value, list) or not commands_value:
    raise TypeError("Bluetooth restart commands must be a non-empty list")
  commands: list[list[str]] = []
  for command in commands_value:
    if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
      raise TypeError("Bluetooth restart commands must be non-empty string lists")
    commands.append(cast(list[str], command))
  if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
    raise TypeError("Bluetooth restart timeout must be a positive integer")
  return {
    "commands": commands,
    "timeout": timeout,
    "unblocking_message": _text(messages.get("unblocking")),
    "usage_message": _text(messages.get("usage")),
    "configuration_error": _text(messages.get("configuration_error")),
    "operation_error": _text(messages.get("operation_error")),
    "success": _status(statuses.get("success")),
    "invalid_arguments": _status(statuses.get("invalid_arguments")),
    "operation_failed": _status(statuses.get("operation_failed")),
  }


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load Bluetooth restart configuration: {error}", file=sys.stderr)
    return 1
  if arguments:
    print(settings["usage_message"], file=sys.stderr)
    return settings["invalid_arguments"]
  print(settings["unblocking_message"])
  try:
    for command in settings["commands"]:
      result = subprocess.run(command, check=False, stdin=subprocess.DEVNULL, timeout=settings["timeout"])
      if result.returncode != settings["success"]:
        return result.returncode
  except (OSError, subprocess.SubprocessError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
