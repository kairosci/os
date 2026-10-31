from __future__ import annotations

import math
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Commands(TypedDict):
  clipboard: list[str]
  paste: list[str]


class Timing(TypedDict):
  clipboard_ready_seconds: float
  paste_settle_seconds: float


class Timeouts(TypedDict):
  paste_seconds: int
  cleanup_seconds: int


class Limits(TypedDict):
  emoji_utf8_bytes: int


class Statuses(TypedDict):
  success: int
  invalid_input: int
  configuration_error: int
  command_error: int


class Messages(TypedDict):
  usage: str
  invalid_input: str
  command_error: str


class Settings(TypedDict):
  commands: Commands
  timing: Timing
  timeouts: Timeouts
  limits: Limits
  statuses: Statuses
  messages: Messages


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"{label} must be a non-empty argv list")
  return cast(list[str], value)


def _duration(value: object, label: str) -> float:
  if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
    raise ValueError(f"{label} must be a finite non-negative duration")
  return float(value)


def _positive_integer(value: object, label: str) -> int:
  if type(value) is not int or value <= 0:
    raise ValueError(f"{label} must be a positive integer")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise ValueError(f"{label} must be an exit status")
  return value


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"{label} must be non-empty text")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/emoji-insert.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "configuration")
  commands = _mapping(document.get("commands"), "commands")
  timing = _mapping(document.get("timing"), "timing")
  timeouts = _mapping(document.get("timeouts"), "timeouts")
  limits = _mapping(document.get("limits"), "limits")
  statuses = _mapping(document.get("statuses"), "statuses")
  messages = _mapping(document.get("messages"), "messages")
  return {
    "commands": {
      "clipboard": _strings(commands.get("clipboard"), "commands.clipboard"),
      "paste": _strings(commands.get("paste"), "commands.paste"),
    },
    "timing": {
      "clipboard_ready_seconds": _duration(timing.get("clipboard_ready_seconds"), "timing.clipboard_ready_seconds"),
      "paste_settle_seconds": _duration(timing.get("paste_settle_seconds"), "timing.paste_settle_seconds"),
    },
    "timeouts": {
      "paste_seconds": _positive_integer(timeouts.get("paste_seconds"), "timeouts.paste_seconds"),
      "cleanup_seconds": _positive_integer(timeouts.get("cleanup_seconds"), "timeouts.cleanup_seconds"),
    },
    "limits": {
      "emoji_utf8_bytes": _positive_integer(limits.get("emoji_utf8_bytes"), "limits.emoji_utf8_bytes"),
    },
    "statuses": {
      "success": _status(statuses.get("success"), "statuses.success"),
      "invalid_input": _status(statuses.get("invalid_input"), "statuses.invalid_input"),
      "configuration_error": _status(statuses.get("configuration_error"), "statuses.configuration_error"),
      "command_error": _status(statuses.get("command_error"), "statuses.command_error"),
    },
    "messages": {
      "usage": _text(messages.get("usage"), "messages.usage"),
      "invalid_input": _text(messages.get("invalid_input"), "messages.invalid_input"),
      "command_error": _text(messages.get("command_error"), "messages.command_error"),
    },
  }


def _stop_process_group(process: subprocess.Popen[bytes], cleanup_seconds: int) -> None:
  try:
    os.killpg(process.pid, signal.SIGTERM)
  except ProcessLookupError:
    pass
  try:
    process.wait(timeout=cleanup_seconds)
  except subprocess.TimeoutExpired:
    try:
      os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
      pass
    process.wait(timeout=cleanup_seconds)
    return
  try:
    os.killpg(process.pid, 0)
  except ProcessLookupError:
    return
  try:
    os.killpg(process.pid, signal.SIGKILL)
  except ProcessLookupError:
    return
  process.wait(timeout=cleanup_seconds)


def _insert(settings: Settings, emoji: bytes) -> int:
  try:
    provider = subprocess.Popen(
      settings["commands"]["clipboard"],
      stdin=subprocess.PIPE,
      start_new_session=True,
    )
  except OSError:
    print(settings["messages"]["command_error"], file=sys.stderr)
    return settings["statuses"]["command_error"]

  if provider.stdin is None:
    _stop_process_group(provider, settings["timeouts"]["cleanup_seconds"])
    print(settings["messages"]["command_error"], file=sys.stderr)
    return settings["statuses"]["command_error"]
  try:
    try:
      provider.stdin.write(emoji)
      provider.stdin.close()
    except OSError:
      print(settings["messages"]["command_error"], file=sys.stderr)
      return settings["statuses"]["command_error"]

    time.sleep(settings["timing"]["clipboard_ready_seconds"])
    try:
      paste = subprocess.Popen(
        settings["commands"]["paste"],
        stderr=subprocess.DEVNULL,
        start_new_session=True,
      )
    except OSError:
      paste = None
    if paste is not None:
      try:
        paste.wait(timeout=settings["timeouts"]["paste_seconds"])
      except subprocess.TimeoutExpired:
        pass
      finally:
        _stop_process_group(paste, settings["timeouts"]["cleanup_seconds"])
    time.sleep(settings["timing"]["paste_settle_seconds"])
    return settings["statuses"]["success"]
  finally:
    if not provider.stdin.closed:
      try:
        provider.stdin.close()
      except OSError:
        pass
    _stop_process_group(provider, settings["timeouts"]["cleanup_seconds"])


def _terminate(signum: int, _frame: object) -> None:
  raise SystemExit(128 + signum)


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  if not arguments or not arguments[0]:
    return settings["statuses"]["success"]
  try:
    emoji = arguments[0].encode("utf-8")
  except UnicodeEncodeError:
    print(settings["messages"]["invalid_input"], file=sys.stderr)
    return settings["statuses"]["invalid_input"]
  if len(emoji) > settings["limits"]["emoji_utf8_bytes"]:
    print(settings["messages"]["invalid_input"], file=sys.stderr)
    return settings["statuses"]["invalid_input"]

  previous_handler = signal.signal(signal.SIGTERM, _terminate)
  try:
    return _insert(settings, emoji)
  finally:
    signal.signal(signal.SIGTERM, previous_handler)
