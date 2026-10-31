from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml

from arch.cli.lib.bounded import run_bounded


class Settings(TypedDict):
  command: list[str]
  timeout_seconds: int
  cleanup_timeout_seconds: int
  max_output_bytes: int
  read_chunk_bytes: int
  blockers_field: str
  lock_blocker: str
  workspace_blocker: str
  locked_status: int
  unlocked_status: int
  undetermined_status: int


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError("configuration must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError("configuration text must be a non-empty string")
  return value


def _strings(value: object) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(part, str) and part for part in value):
    raise ValueError("command must be a non-empty list of strings")
  return cast(list[str], value)


def _positive_integer(value: object) -> int:
  if type(value) is not int or value <= 0:
    raise ValueError("configuration value must be a positive integer")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hyprland-session-locked.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  fields = _mapping(document.get("fields"))
  blockers = _mapping(document.get("blockers"))
  statuses = _mapping(document.get("statuses"))
  locked = statuses.get("locked")
  unlocked = statuses.get("unlocked")
  undetermined = statuses.get("undetermined")
  if set(statuses) != {"locked", "unlocked", "undetermined"}:
    raise ValueError("statuses must define locked, unlocked, and undetermined results")
  if type(locked) is not int or locked != 0 or type(unlocked) is not int or unlocked <= 0:
    raise ValueError("locked status must be zero and unlocked status must be positive")
  if type(undetermined) is not int or undetermined <= 0:
    raise ValueError("undetermined status must be positive")
  if len({locked, unlocked, undetermined}) != len(statuses):
    raise ValueError("session lock result statuses must be distinct")
  return {
    "command": _strings(document.get("command")),
    "timeout_seconds": _positive_integer(document.get("timeout_seconds")),
    "cleanup_timeout_seconds": _positive_integer(document.get("cleanup_timeout_seconds")),
    "max_output_bytes": _positive_integer(document.get("max_output_bytes")),
    "read_chunk_bytes": _positive_integer(document.get("read_chunk_bytes")),
    "blockers_field": _text(fields.get("blockers")),
    "lock_blocker": _text(blockers.get("lock")),
    "workspace_blocker": _text(blockers.get("workspace")),
    "locked_status": locked,
    "unlocked_status": unlocked,
    "undetermined_status": undetermined,
  }


def _state(monitors: object, settings: Settings) -> int:
  if not isinstance(monitors, list):
    return settings["undetermined_status"]
  has_readable_monitor = False
  for monitor in monitors:
    if not isinstance(monitor, dict):
      return settings["undetermined_status"]
    blockers: object = monitor.get(settings["blockers_field"])
    if blockers is None:
      blockers = []
    if not isinstance(blockers, list):
      return settings["undetermined_status"]
    if settings["lock_blocker"] in blockers:
      return settings["locked_status"]
    has_readable_monitor |= settings["workspace_blocker"] not in blockers
  if has_readable_monitor:
    return settings["unlocked_status"]
  return settings["undetermined_status"]


def main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG
  try:
    output = run_bounded(
      settings["command"],
      timeout_seconds=settings["timeout_seconds"],
      cleanup_timeout_seconds=settings["cleanup_timeout_seconds"],
      max_output_bytes=settings["max_output_bytes"],
      read_chunk_bytes=settings["read_chunk_bytes"],
    )
  except OSError:
    return settings["undetermined_status"]
  if output is None:
    return settings["undetermined_status"]
  try:
    monitors: object = json.loads(output)
  except (UnicodeError, ValueError):
    return settings["undetermined_status"]
  return _state(monitors, settings)
