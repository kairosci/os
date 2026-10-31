from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Commands(TypedDict):
  language: list[str]
  timestamp: list[str]
  date: list[str]
  translation: list[str]
  notification: list[str]


class Formats(TypedDict):
  day_time: str
  day_month_year: str
  week_number: str


class Settings(TypedDict):
  commands: Commands
  formats: Formats
  timeout_seconds: int
  statuses: dict[str, int]
  messages: dict[str, str]


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError("configuration must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _strings(value: object) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(part, str) and part for part in value):
    raise ValueError("command must be a non-empty list of strings")
  return cast(list[str], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError("value must be a non-empty string")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/notification-time.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  commands = _mapping(document.get("commands"))
  formats = _mapping(document.get("formats"))
  statuses = _mapping(document.get("statuses"))
  messages = _mapping(document.get("messages"))
  timeout = document.get("timeout_seconds")
  if type(timeout) is not int or timeout <= 0:
    raise ValueError("timeout_seconds must be a positive integer")
  success = statuses.get("success")
  failure = statuses.get("failure")
  if type(success) is not int or success < 0 or type(failure) is not int or failure <= 0:
    raise ValueError("statuses must define a non-negative success code and a positive failure code")
  return {
    "commands": {
      "language": _strings(commands.get("language")),
      "timestamp": _strings(commands.get("timestamp")),
      "date": _strings(commands.get("date")),
      "translation": _strings(commands.get("translation")),
      "notification": _strings(commands.get("notification")),
    },
    "formats": {
      "day_time": _text(formats.get("day_time")),
      "day_month_year": _text(formats.get("day_month_year")),
      "week_number": _text(formats.get("week_number")),
    },
    "timeout_seconds": timeout,
    "statuses": {"success": success, "failure": failure},
    "messages": {
      "invalid_arguments": _text(messages.get("invalid_arguments")),
      "operation_error": _text(messages.get("operation_error")),
    },
  }


def _run(command: list[str], deadline: float, *, locale: str | None = None) -> str:
  remaining = deadline - time.monotonic()
  if remaining <= 0:
    raise subprocess.TimeoutExpired(command, 0)
  environment = os.environ.copy()
  if locale is not None:
    environment["LC_TIME"] = locale
  result = subprocess.run(
    command,
    check=False,
    capture_output=True,
    text=True,
    timeout=remaining,
    env=environment,
  )
  if result.returncode != 0:
    raise subprocess.SubprocessError(f"{command[0]} exited with status {result.returncode}")
  return result.stdout.rstrip("\n")


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  if arguments:
    print(settings["messages"]["invalid_arguments"], file=sys.stderr)
    return settings["statuses"]["failure"]

  try:
    commands = settings["commands"]
    deadline = time.monotonic() + settings["timeout_seconds"]
    locale = _run(commands["language"], deadline)
    timestamp = _run(commands["timestamp"], deadline)
    date_command = commands["date"] + [f"@{timestamp}"]
    day_time = _run(date_command + [settings["formats"]["day_time"]], deadline, locale=locale)
    day_month_year = _run(date_command + [settings["formats"]["day_month_year"]], deadline, locale=locale)
    week_number = _run(date_command + [settings["formats"]["week_number"]], deadline, locale=locale)
    message = _run(commands["translation"] + [day_time, day_month_year, week_number], deadline)
    _run(commands["notification"] + [message], deadline)
    return settings["statuses"]["success"]
  except (OSError, subprocess.SubprocessError, UnicodeError, ValueError) as error:
    print(f"{settings['messages']['operation_error']}: {error}", file=sys.stderr)
    return settings["statuses"]["failure"]
