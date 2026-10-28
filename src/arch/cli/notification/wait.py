from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TypeGuard, TypedDict

import yaml


class ArgumentCounts(TypedDict):
  maximum: int


class ExitCodes(TypedDict):
  usage: int
  invalid_timeout: int
  timeout: int


class NotificationWaitConfig(TypedDict):
  default_timeout_seconds: int
  maximum_timeout_seconds: int
  probe_interval_seconds: float
  default_language: str
  argument_counts: ArgumentCounts
  probe_commands: list[list[str]]
  exit_codes: ExitCodes
  messages: dict[str, dict[str, str]]


def _is_string_mapping(value: object) -> TypeGuard[dict[str, str]]:
  return isinstance(value, dict) and all(
    isinstance(key, str) and isinstance(item, str) for key, item in value.items()
  )


def _is_integer_mapping(value: object, required_keys: set[str]) -> TypeGuard[dict[str, int]]:
  return (
    isinstance(value, dict)
    and required_keys.issubset(value)
    and all(isinstance(key, str) and type(item) is int for key, item in value.items())
  )


def _is_notification_wait_config(value: object) -> TypeGuard[NotificationWaitConfig]:
  if not isinstance(value, dict):
    return False
  default_timeout = value.get("default_timeout_seconds")
  maximum_timeout = value.get("maximum_timeout_seconds")
  probe_interval = value.get("probe_interval_seconds")
  default_language = value.get("default_language")
  argument_counts = value.get("argument_counts")
  probe_commands = value.get("probe_commands")
  exit_codes = value.get("exit_codes")
  messages = value.get("messages")
  if (
    type(default_timeout) is not int
    or type(maximum_timeout) is not int
    or not isinstance(probe_interval, float)
    or not isinstance(default_language, str)
    or not _is_integer_mapping(argument_counts, {"maximum"})
    or not _is_integer_mapping(exit_codes, {"usage", "invalid_timeout", "timeout"})
    or not isinstance(probe_commands, list)
    or not all(
      isinstance(command, list) and all(isinstance(part, str) for part in command)
      for command in probe_commands
    )
    or not isinstance(messages, dict)
    or not all(isinstance(language, str) and _is_string_mapping(entries) for language, entries in messages.items())
  ):
    return False
  return True


def _config() -> NotificationWaitConfig:
  root = Path(os.environ["ARCH_PATH"])
  config: object = yaml.safe_load((root / "data/cli/notification-wait.yml").read_text(encoding="utf-8"))
  if not _is_notification_wait_config(config):
    raise ValueError("invalid notification wait configuration")
  return config


def _ready(config: NotificationWaitConfig) -> bool:
  for command in config["probe_commands"]:
    try:
      status = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode
    except OSError:
      return False
    if status != 0:
      return False
  return True


def _message(config: NotificationWaitConfig, key: str) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  messages = config["messages"]
  language = language if language in messages else config["default_language"]
  return messages[language][key]


def main() -> int:
  config = _config()
  if len(sys.argv) > config["argument_counts"]["maximum"]:
    print(_message(config, "usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]

  try:
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else config["default_timeout_seconds"]
  except ValueError:
    print(_message(config, "invalid_timeout"), file=sys.stderr)
    return config["exit_codes"]["invalid_timeout"]
  if timeout < 0 or timeout > config["maximum_timeout_seconds"]:
    print(_message(config, "invalid_timeout"), file=sys.stderr)
    return config["exit_codes"]["invalid_timeout"]

  deadline = time.monotonic() + timeout
  while time.monotonic() < deadline:
    if _ready(config):
      return 0
    remaining = deadline - time.monotonic()
    if remaining > 0:
      time.sleep(min(config["probe_interval_seconds"], remaining))
  return config["exit_codes"]["timeout"]


if __name__ == "__main__":
  raise SystemExit(main())
