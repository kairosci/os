from __future__ import annotations

import os
import re
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
  profile_line_pattern: re.Pattern[str]
  active_state_option: str
  usage: str
  success_status: int
  invalid_arguments_status: int


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
  raw: object = yaml.safe_load((root / "data/cli/powerprofiles-list.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  statuses = _mapping(document.get("statuses"))
  success = statuses.get("success")
  invalid_arguments = statuses.get("invalid_arguments")
  if type(success) is not int or success != 0 or type(invalid_arguments) is not int or invalid_arguments <= 0:
    raise ValueError("statuses must define a zero success code and a positive argument error code")
  pattern = re.compile(_text(document.get("profile_line_pattern")))
  if not {"active", "name"} <= pattern.groupindex.keys():
    raise ValueError("profile_line_pattern must define active and name groups")
  return {
    "command": _strings(document.get("command")),
    "timeout_seconds": _positive_integer(document.get("timeout_seconds")),
    "cleanup_timeout_seconds": _positive_integer(document.get("cleanup_timeout_seconds")),
    "max_output_bytes": _positive_integer(document.get("max_output_bytes")),
    "read_chunk_bytes": _positive_integer(document.get("read_chunk_bytes")),
    "profile_line_pattern": pattern,
    "active_state_option": _text(document.get("active_state_option")),
    "usage": _text(document.get("usage")),
    "success_status": success,
    "invalid_arguments_status": invalid_arguments,
  }


def _profiles(settings: Settings, with_state: bool) -> str:
  try:
    output = run_bounded(
      settings["command"],
      timeout_seconds=settings["timeout_seconds"],
      cleanup_timeout_seconds=settings["cleanup_timeout_seconds"],
      max_output_bytes=settings["max_output_bytes"],
      read_chunk_bytes=settings["read_chunk_bytes"],
    )
  except OSError:
    return ""
  if output is None:
    return ""

  profiles: list[tuple[str, bool]] = []
  for line in output.decode("utf-8", errors="replace").splitlines():
    match = settings["profile_line_pattern"].fullmatch(line)
    if match is not None:
      profiles.append((match.group("name"), bool(match.group("active"))))
  return "\n".join(
    f"{name}\t{int(active)}" if with_state else name
    for name, active in reversed(profiles)
  )


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG
  if any(argument != settings["active_state_option"] for argument in arguments) or len(arguments) > 1:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments_status"]
  output = _profiles(settings, settings["active_state_option"] in arguments)
  if output:
    print(output)
  return settings["success_status"]
