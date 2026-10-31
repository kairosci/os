from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Commands(TypedDict):
  battery_status: list[str]
  notification: list[str]


class Messages(TypedDict):
  operation_error: str
  empty_status: str


class Settings(TypedDict):
  commands: Commands
  timeout_seconds: int
  failure_status: int
  messages: Messages


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
  raw: object = yaml.safe_load((root / "data/cli/notification-battery.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  commands = _mapping(document.get("commands"))
  messages = _mapping(document.get("messages"))
  timeout = document.get("timeout_seconds")
  failure_status = document.get("failure_status")
  if type(timeout) is not int or timeout <= 0:
    raise ValueError("timeout_seconds must be a positive integer")
  if type(failure_status) is not int or failure_status <= 0:
    raise ValueError("failure_status must be a positive integer")
  return {
    "commands": {
      "battery_status": _strings(commands.get("battery_status")),
      "notification": _strings(commands.get("notification")),
    },
    "timeout_seconds": timeout,
    "failure_status": failure_status,
    "messages": {
      "operation_error": _text(messages.get("operation_error")),
      "empty_status": _text(messages.get("empty_status")),
    },
  }


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  deadline = time.monotonic() + settings["timeout_seconds"]
  try:
    battery = subprocess.run(
      settings["commands"]["battery_status"],
      check=False,
      capture_output=True,
      text=True,
      timeout=settings["timeout_seconds"],
    )
    if battery.returncode != 0:
      raise subprocess.SubprocessError(f"{settings['commands']['battery_status'][0]} exited with status {battery.returncode}")
    status = battery.stdout.rstrip("\n")
    if not status:
      print(settings["messages"]["empty_status"], file=sys.stderr)
      return settings["failure_status"]
    remaining = deadline - time.monotonic()
    if remaining <= 0:
      raise subprocess.TimeoutExpired(settings["commands"]["notification"], 0)
    notification = subprocess.run(
      settings["commands"]["notification"] + [status],
      check=False,
      timeout=remaining,
    )
    return notification.returncode
  except (OSError, subprocess.SubprocessError, UnicodeError, ValueError) as error:
    print(f"{settings['messages']['operation_error']}: {error}", file=sys.stderr)
    return settings["failure_status"]
