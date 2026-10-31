from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import cast

import yaml
from arch.cli.lib.bounded import run_bounded


def _settings() -> dict[str, object]:
  root = Path(os.environ["AP"])
  document: object = yaml.safe_load(
    (root / "data/cli/notification-silencing-toggle.yml").read_text(encoding="utf-8")
  )
  if not isinstance(document, dict):
    raise ValueError("invalid notification silencing configuration")
  sections = {name: document.get(name) for name in ("commands", "limits", "messages", "statuses")}
  if not all(isinstance(value, dict) for value in sections.values()):
    raise ValueError("incomplete notification silencing configuration")
  commands = cast(dict[str, object], sections["commands"])
  limits = cast(dict[str, object], sections["limits"])
  messages = cast(dict[str, object], sections["messages"])
  statuses = cast(dict[str, object], sections["statuses"])
  parsed_commands: dict[str, list[str]] = {}
  for name in ("toggle", "refresh"):
    command = commands.get(name)
    if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
      raise ValueError(f"invalid notification silencing command: {name}")
    parsed_commands[name] = cast(list[str], command)
  for name in ("command_timeout_seconds", "cleanup_timeout_seconds", "maximum_output_bytes", "read_chunk_bytes"):
    if type(limits.get(name)) is not int or cast(int, limits[name]) <= 0:
      raise ValueError(f"invalid notification silencing limit: {name}")
  for name in ("usage", "refresh_error"):
    if not isinstance(messages.get(name), str) or not messages[name]:
      raise ValueError(f"incomplete notification silencing message: {name}")
  for name in ("invalid_arguments", "refresh_error", "success"):
    if type(statuses.get(name)) is not int or not 0 <= cast(int, statuses[name]) <= 255:
      raise ValueError(f"invalid notification silencing status: {name}")
  return {"commands": parsed_commands, "limits": limits, "messages": messages, "statuses": statuses}


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not load notification silencing configuration", file=sys.stderr)
    return os.EX_CONFIG
  messages = cast(dict[str, str], settings["messages"])
  statuses = cast(dict[str, int], settings["statuses"])
  if arguments:
    print(messages["usage"], file=sys.stderr)
    return statuses["invalid_arguments"]
  commands = cast(dict[str, list[str]], settings["commands"])
  limits = cast(dict[str, int], settings["limits"])
  bounded = {
    "timeout_seconds": limits["command_timeout_seconds"],
    "cleanup_timeout_seconds": limits["cleanup_timeout_seconds"],
    "max_output_bytes": limits["maximum_output_bytes"],
    "read_chunk_bytes": limits["read_chunk_bytes"],
  }
  run_bounded(commands["toggle"], **bounded)
  refreshed = run_bounded(commands["refresh"], **bounded)
  if refreshed is None:
    print(messages["refresh_error"], file=sys.stderr)
    return statuses["refresh_error"]
  return statuses["success"]
