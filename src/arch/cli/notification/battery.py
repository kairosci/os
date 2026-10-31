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
  low_title: list[str]
  low_body: list[str]
  low_notification: list[str]
  low_notification_suffix: list[str]
  low_hook: list[str]


class Messages(TypedDict):
  operation_error: str
  empty_status: str
  low_usage: str
  low_operation_error: str


class Settings(TypedDict):
  commands: Commands
  timeout_seconds: int
  failure_status: int
  low_argument_count: int
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
  low_battery = _mapping(document.get("low_battery"))
  low_commands = _mapping(low_battery.get("commands"))
  timeout = document.get("timeout_seconds")
  failure_status = document.get("failure_status")
  low_argument_count = low_battery.get("argument_count")
  if type(timeout) is not int or timeout <= 0:
    raise ValueError("timeout_seconds must be a positive integer")
  if type(failure_status) is not int or failure_status <= 0:
    raise ValueError("failure_status must be a positive integer")
  if type(low_argument_count) is not int or low_argument_count <= 0:
    raise ValueError("low_battery.argument_count must be a positive integer")
  return {
    "commands": {
      "battery_status": _strings(commands.get("battery_status")),
      "notification": _strings(commands.get("notification")),
      "low_title": _strings(low_commands.get("title")),
      "low_body": _strings(low_commands.get("body")),
      "low_notification": _strings(low_commands.get("notification")),
      "low_notification_suffix": _strings(low_commands.get("notification_suffix")),
      "low_hook": _strings(low_commands.get("hook")),
    },
    "timeout_seconds": timeout,
    "failure_status": failure_status,
    "low_argument_count": low_argument_count,
    "messages": {
      "operation_error": _text(messages.get("operation_error")),
      "empty_status": _text(messages.get("empty_status")),
      "low_usage": _text(low_battery.get("usage")),
      "low_operation_error": _text(low_battery.get("operation_error")),
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


def low_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return os.EX_CONFIG

  if len(arguments) != settings["low_argument_count"]:
    print(settings["messages"]["low_usage"], file=sys.stderr)
    return settings["failure_status"]

  deadline = time.monotonic() + settings["timeout_seconds"]
  commands = settings["commands"]
  try:
    title = _run_before_deadline(commands["low_title"], deadline, capture=True)
    body = _run_before_deadline([*commands["low_body"], arguments[0]], deadline, capture=True)
    notification = _run_before_deadline(
      [
        *commands["low_notification"],
        title.stdout.rstrip("\n"),
        body.stdout.rstrip("\n"),
        *commands["low_notification_suffix"],
      ],
      deadline,
    )
    if notification.returncode != 0:
      return notification.returncode
    hook = _run_before_deadline([*commands["low_hook"], arguments[0]], deadline)
    return hook.returncode
  except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
    print(settings["messages"]["low_operation_error"], file=sys.stderr)
    return settings["failure_status"]


def _run_before_deadline(
  command: list[str], deadline: float, *, capture: bool = False
) -> subprocess.CompletedProcess[str]:
  remaining = deadline - time.monotonic()
  if remaining <= 0:
    raise subprocess.TimeoutExpired(command, 0)
  return subprocess.run(
    command,
    check=False,
    capture_output=capture,
    text=True,
    timeout=remaining,
  )
