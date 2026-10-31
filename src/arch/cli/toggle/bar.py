from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import cast

import yaml
from arch.cli.lib.bounded import run_bounded


def _settings() -> dict[str, object]:
  root = Path(os.environ["AP"])
  document: object = yaml.safe_load((root / "data/cli/bar-toggle.yml").read_text(encoding="utf-8"))
  if not isinstance(document, dict):
    raise ValueError("invalid bar toggle configuration")
  commands, values, limits, messages, statuses = (
    document.get(key) for key in ("commands", "values", "limits", "messages", "statuses")
  )
  if not all(isinstance(section, dict) for section in (commands, values, limits, messages, statuses)):
    raise ValueError("incomplete bar toggle configuration")
  commands = cast(dict[str, object], commands)
  values = cast(dict[str, object], values)
  limits = cast(dict[str, object], limits)
  messages = cast(dict[str, object], messages)
  statuses = cast(dict[str, object], statuses)
  parsed_commands: dict[str, list[str]] = {}
  for name in ("set_state", "refresh"):
    command = commands.get(name)
    if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
      raise ValueError(f"invalid bar command: {name}")
    parsed_commands[name] = cast(list[str], command)
  for name in ("command_timeout_seconds", "cleanup_timeout_seconds", "maximum_output_bytes", "read_chunk_bytes"):
    if type(limits.get(name)) is not int or cast(int, limits[name]) <= 0:
      raise ValueError(f"invalid bar limit: {name}")
  for name in ("invalid_arguments", "command_error", "success"):
    if type(statuses.get(name)) is not int or not 0 <= cast(int, statuses[name]) <= 255:
      raise ValueError(f"invalid bar status: {name}")
  actions = values.get("actions")
  if not isinstance(actions, list) or not actions or not all(isinstance(item, str) and item for item in actions):
    raise ValueError("invalid bar actions")
  if values.get("default_action") not in actions or not isinstance(messages.get("usage"), str):
    raise ValueError("incomplete bar toggle values")
  if not isinstance(messages.get("command_error"), str):
    raise ValueError("incomplete bar toggle messages")
  return {
    "commands": parsed_commands,
    "default_action": values["default_action"],
    "actions": actions,
    "limits": limits,
    "messages": messages,
    "statuses": statuses,
  }


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not load bar toggle configuration", file=sys.stderr)
    return os.EX_CONFIG
  messages = cast(dict[str, str], settings["messages"])
  statuses = cast(dict[str, int], settings["statuses"])
  action = arguments[0] if arguments else cast(str, settings["default_action"])
  if len(arguments) > 1 or action not in cast(list[str], settings["actions"]):
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
  state = run_bounded([*commands["set_state"], action], **bounded)
  if state is None:
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  run_bounded(commands["refresh"], **bounded)
  return statuses["success"]
