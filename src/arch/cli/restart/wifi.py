from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Command(TypedDict):
  argv: list[str]
  ignore_failure: bool
  suppress_stderr: bool


class Settings(TypedDict):
  commands: list[Command]
  command_timeout: int
  operation_timeout: int
  unblocking_message: str
  usage_message: str
  configuration_error: str
  operation_error: str
  success: int
  invalid_arguments: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"Wi-Fi restart {label} must be a mapping")
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError("Wi-Fi restart messages must be non-empty strings")
  return value


def _positive_integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 1:
    raise TypeError(f"Wi-Fi restart {label} must be a positive integer")
  return value


def _status(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise TypeError("Wi-Fi restart statuses must be non-negative integers")
  return value


def _settings(document: dict[str, object]) -> Settings:
  limits = _mapping(document.get("limits"), "limits")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  command_values = document.get("commands")
  if not isinstance(command_values, list) or not command_values:
    raise TypeError("Wi-Fi restart commands must be a non-empty list")
  commands: list[Command] = []
  for command_value in command_values:
    command = _mapping(command_value, "command")
    argv = command.get("argv")
    ignore_failure = command.get("ignore_failure")
    suppress_stderr = command.get("suppress_stderr", False)
    if not isinstance(argv, list) or not argv or not all(isinstance(part, str) and part for part in argv):
      raise TypeError("Wi-Fi restart argv must be a non-empty list of strings")
    if not isinstance(ignore_failure, bool) or not isinstance(suppress_stderr, bool):
      raise TypeError("Wi-Fi restart command flags must be booleans")
    commands.append({
      "argv": cast(list[str], argv),
      "ignore_failure": ignore_failure,
      "suppress_stderr": suppress_stderr,
    })
  required_command = commands[-1]
  if required_command["ignore_failure"]:
    raise TypeError("The final Wi-Fi status command must report its failure")
  return {
    "commands": commands,
    "command_timeout": _positive_integer(limits.get("command_timeout_seconds"), "command timeout"),
    "operation_timeout": _positive_integer(limits.get("operation_timeout_seconds"), "operation timeout"),
    "unblocking_message": _text(messages.get("unblocking")),
    "usage_message": _text(messages.get("usage")),
    "configuration_error": _text(messages.get("configuration_error")),
    "operation_error": _text(messages.get("operation_error")),
    "success": _status(statuses.get("success")),
    "invalid_arguments": _status(statuses.get("invalid_arguments")),
    "operation_failed": _status(statuses.get("operation_failed")),
  }


def main(arguments: list[str]) -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load((root / "data/cli/restart-wifi.yml").read_text(encoding="utf-8"))
    document = _mapping(raw, "settings")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"))
    settings = _settings(document)
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    if configuration_error:
      print(configuration_error.format(error=error), file=sys.stderr)
    else:
      print(error, file=sys.stderr)
    return 1
  if arguments:
    print(settings["usage_message"], file=sys.stderr)
    return settings["invalid_arguments"]

  print(settings["unblocking_message"], end="\n\n", flush=True)
  deadline = time.monotonic() + settings["operation_timeout"]
  try:
    for command in settings["commands"]:
      remaining = deadline - time.monotonic()
      if remaining <= 0:
        raise subprocess.TimeoutExpired(command["argv"], settings["operation_timeout"])
      try:
        result = subprocess.run(
          command["argv"],
          check=False,
          stdin=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL if command["suppress_stderr"] else None,
          timeout=min(settings["command_timeout"], remaining),
        )
      except subprocess.TimeoutExpired:
        if command["ignore_failure"] and time.monotonic() < deadline:
          continue
        raise
      if result.returncode != settings["success"] and not command["ignore_failure"]:
        return result.returncode
  except (OSError, subprocess.SubprocessError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
