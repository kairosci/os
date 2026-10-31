from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Statuses(TypedDict):
  missing_argument: int
  timeout: int
  command_error: int


class Messages(TypedDict):
  usage: str
  timeout: str
  command_error: str


class Settings(TypedDict):
  command: list[str]
  timeout_seconds: int
  statuses: Statuses
  messages: Messages


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError("configuration must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError("value must be a non-empty string")
  return value


def _strings(value: object) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(part, str) and part for part in value):
    raise ValueError("command must be a non-empty list of strings")
  return cast(list[str], value)


def _positive_integer(value: object) -> int:
  if type(value) is not int or value <= 0:
    raise ValueError("value must be a positive integer")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/notification-dismiss.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  statuses = _mapping(document.get("statuses"))
  messages = _mapping(document.get("messages"))
  timeout = document.get("timeout_seconds")
  missing_argument = _positive_integer(statuses.get("missing_argument"))
  command_error = _positive_integer(statuses.get("command_error"))
  timeout_status = _positive_integer(statuses.get("timeout"))
  if type(timeout) is not int or timeout <= 0:
    raise ValueError("timeout_seconds must be a positive integer")
  return {
    "command": _strings(document.get("command")),
    "timeout_seconds": timeout,
    "statuses": {
      "missing_argument": missing_argument,
      "command_error": command_error,
      "timeout": timeout_status,
    },
    "messages": {
      "usage": _text(messages.get("usage")),
      "timeout": _text(messages.get("timeout")),
      "command_error": _text(messages.get("command_error")),
    },
  }


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  if not arguments:
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["missing_argument"]

  try:
    result = subprocess.run(
      settings["command"] + [arguments[0]],
      check=False,
      timeout=settings["timeout_seconds"],
    )
  except subprocess.TimeoutExpired:
    print(settings["messages"]["timeout"], file=sys.stderr)
    return settings["statuses"]["timeout"]
  except OSError as error:
    print(f"{settings['messages']['command_error']}: {error}", file=sys.stderr)
    return settings["statuses"]["command_error"]
  return result.returncode
