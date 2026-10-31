from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml

from arch.cli.lib.bounded import run_bounded


class Limits(TypedDict):
  command_timeout_seconds: int
  cleanup_timeout_seconds: int
  maximum_output_bytes: int
  read_chunk_bytes: int


class SpaceGuardSettings(TypedDict):
  command: list[str]
  force_environment: str
  force_value: str
  minimum_available_bytes: int
  available_bytes_pattern: str
  limits: Limits
  messages: dict[str, str]
  statuses: dict[str, int]


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"invalid update space guard configuration: {label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"invalid update space guard configuration: {label} must be non-empty text")
  return value


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise TypeError(f"invalid update space guard configuration: {label} must be a non-empty string list")
  return cast(list[str], value)


def _positive_integer(value: object, label: str) -> int:
  if type(value) is not int or value <= 0:
    raise TypeError(f"invalid update space guard configuration: {label} must be a positive integer")
  return value


def _settings() -> SpaceGuardSettings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load(
    (root / "data/cli/update-space-guard.yml").read_text(encoding="utf-8")
  )
  document = _mapping(raw, "root")
  raw_settings = _mapping(document.get("space_guard"), "space_guard")
  raw_limits = _mapping(raw_settings.get("limits"), "space_guard.limits")
  raw_messages = _mapping(raw_settings.get("messages"), "space_guard.messages")
  raw_statuses = _mapping(raw_settings.get("statuses"), "space_guard.statuses")
  pattern = _text(raw_settings.get("available_bytes_pattern"), "space_guard.available_bytes_pattern")
  re.compile(pattern)
  limits: Limits = {
    "command_timeout_seconds": _positive_integer(
      raw_limits.get("command_timeout_seconds"), "space_guard.limits.command_timeout_seconds"
    ),
    "cleanup_timeout_seconds": _positive_integer(
      raw_limits.get("cleanup_timeout_seconds"), "space_guard.limits.cleanup_timeout_seconds"
    ),
    "maximum_output_bytes": _positive_integer(
      raw_limits.get("maximum_output_bytes"), "space_guard.limits.maximum_output_bytes"
    ),
    "read_chunk_bytes": _positive_integer(
      raw_limits.get("read_chunk_bytes"), "space_guard.limits.read_chunk_bytes"
    ),
  }
  messages = {key: _text(value, f"space_guard.messages.{key}") for key, value in raw_messages.items()}
  if set(messages) != {"low_space", "usage"}:
    raise ValueError("invalid update space guard configuration: messages are incomplete")
  statuses = {
    key: value
    for key, value in raw_statuses.items()
    if type(value) is int and 0 <= value <= 255
  }
  if set(statuses) != {"success", "insufficient_space", "invalid_arguments"}:
    raise ValueError("invalid update space guard configuration: statuses are incomplete")
  if len(set(statuses.values())) != len(statuses):
    raise ValueError("invalid update space guard configuration: statuses must be distinct")
  return {
    "command": _strings(raw_settings.get("command"), "space_guard.command"),
    "force_environment": _text(raw_settings.get("force_environment"), "space_guard.force_environment"),
    "force_value": _text(raw_settings.get("force_value"), "space_guard.force_value"),
    "minimum_available_bytes": _positive_integer(
      raw_settings.get("minimum_available_bytes"), "space_guard.minimum_available_bytes"
    ),
    "available_bytes_pattern": pattern,
    "limits": limits,
    "messages": messages,
    "statuses": statuses,
  }


def available_bytes(settings: SpaceGuardSettings) -> int | None:
  limits = settings["limits"]
  output = run_bounded(
    settings["command"],
    timeout_seconds=limits["command_timeout_seconds"],
    cleanup_timeout_seconds=limits["cleanup_timeout_seconds"],
    max_output_bytes=limits["maximum_output_bytes"],
    read_chunk_bytes=limits["read_chunk_bytes"],
  )
  if output is None:
    return None
  lines = output.decode("utf-8", errors="replace").splitlines()
  if not lines or not re.fullmatch(settings["available_bytes_pattern"], lines[-1]):
    return None
  return int(lines[-1])


def main(arguments: list[str] | None = None) -> int:
  settings = _settings()
  arguments = sys.argv[1:] if arguments is None else arguments
  if arguments:
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]
  if os.environ.get(settings["force_environment"]) == settings["force_value"]:
    return settings["statuses"]["success"]
  free_bytes = available_bytes(settings)
  if free_bytes is not None and free_bytes < settings["minimum_available_bytes"]:
    print(settings["messages"]["low_space"])
    return settings["statuses"]["insufficient_space"]
  return settings["statuses"]["success"]
