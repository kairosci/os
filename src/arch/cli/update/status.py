from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  command: list[str]
  command_error: int
  command_error_message: str


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  document = _mapping(yaml.safe_load((root / "data/cli/update-status.yml").read_text(encoding="utf-8")), "configuration")
  statuses = _mapping(document.get("statuses"), "statuses")
  messages = _mapping(document.get("messages"), "messages")
  command = document.get("command")
  command_error = statuses.get("command_error")
  command_error_message = messages.get("command_error")
  if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
    raise ValueError("command must be a non-empty argv list")
  if type(command_error) is not int or not 0 <= command_error <= 255:
    raise ValueError("command_error must be an exit status")
  if not isinstance(command_error_message, str) or not command_error_message:
    raise ValueError("messages.command_error must be non-empty text")
  return {
    "command": cast(list[str], command),
    "command_error": command_error,
    "command_error_message": command_error_message,
  }


def main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  try:
    return subprocess.run(settings["command"], check=False).returncode
  except OSError:
    print(settings["command_error_message"], file=sys.stderr)
    return settings["command_error"]
