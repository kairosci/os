from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import cast

import yaml
from arch.cli.lib.bounded import run_bounded
from arch.cli.toggle.state import is_enabled


def _settings() -> dict[str, object]:
  root = Path(os.environ["AP"])
  document: object = yaml.safe_load((root / "data/cli/crash-capture-toggle.yml").read_text(encoding="utf-8"))
  if not isinstance(document, dict):
    raise ValueError("invalid crash capture toggle configuration")
  sections = {name: document.get(name) for name in ("commands", "values", "limits", "messages", "statuses")}
  if not all(isinstance(value, dict) for value in sections.values()):
    raise ValueError("incomplete crash capture toggle configuration")
  commands = cast(dict[str, object], sections["commands"])
  values = cast(dict[str, object], sections["values"])
  limits = cast(dict[str, object], sections["limits"])
  messages = cast(dict[str, object], sections["messages"])
  statuses = cast(dict[str, object], sections["statuses"])
  parsed_commands: dict[str, list[str]] = {}
  for name in ("set_state", "systemctl", "localize", "notify"):
    command = commands.get(name)
    if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
      raise ValueError(f"invalid crash capture command: {name}")
    parsed_commands[name] = cast(list[str], command)
  text_values = ("flag_name", "unit_name", "toggle_action", "disabled_key", "enabled_key", "notification_glyph")
  if not all(isinstance(values.get(name), str) and values[name] for name in text_values):
    raise ValueError("incomplete crash capture values")
  state_effects = values.get("state_effects")
  service_actions = values.get("service_actions")
  if (
    not isinstance(state_effects, dict)
    or not isinstance(service_actions, dict)
    or not {"enabled", "disabled"} <= set(state_effects)
    or not all(isinstance(item, str) and item for item in (*state_effects.values(), *service_actions.values()))
    or not set(state_effects.values()) <= set(service_actions)
  ):
    raise ValueError("invalid crash capture service actions")
  for name in ("command_timeout_seconds", "cleanup_timeout_seconds", "maximum_output_bytes", "read_chunk_bytes"):
    if type(limits.get(name)) is not int or cast(int, limits[name]) <= 0:
      raise ValueError(f"invalid crash capture limit: {name}")
  for name in ("usage", "command_error"):
    if not isinstance(messages.get(name), str) or not messages[name]:
      raise ValueError(f"incomplete crash capture message: {name}")
  for name in ("invalid_arguments", "command_error", "success"):
    if type(statuses.get(name)) is not int or not 0 <= cast(int, statuses[name]) <= 255:
      raise ValueError(f"invalid crash capture status: {name}")
  return {
    "commands": parsed_commands,
    "values": values,
    "limits": limits,
    "messages": messages,
    "statuses": statuses,
  }


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not load crash capture toggle configuration", file=sys.stderr)
    return os.EX_CONFIG
  commands = cast(dict[str, list[str]], settings["commands"])
  values = cast(dict[str, object], settings["values"])
  limits = cast(dict[str, int], settings["limits"])
  messages = cast(dict[str, str], settings["messages"])
  statuses = cast(dict[str, int], settings["statuses"])
  if arguments:
    print(messages["usage"], file=sys.stderr)
    return statuses["invalid_arguments"]
  bounded = {
    "timeout_seconds": limits["command_timeout_seconds"],
    "cleanup_timeout_seconds": limits["cleanup_timeout_seconds"],
    "max_output_bytes": limits["maximum_output_bytes"],
    "read_chunk_bytes": limits["read_chunk_bytes"],
  }
  state = run_bounded(
    [*commands["set_state"], cast(str, values["flag_name"]), cast(str, values["toggle_action"])],
    **bounded,
  )
  if state is None:
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  try:
    flag_enabled = is_enabled(cast(str, values["flag_name"]))
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  state_name = "enabled" if flag_enabled else "disabled"
  effects = cast(dict[str, str], values["state_effects"])
  service_actions = cast(dict[str, str], values["service_actions"])
  service_action = service_actions[effects[state_name]]
  service = run_bounded(
    [*commands["systemctl"], service_action, cast(str, values["unit_name"])], **bounded
  )
  if service is None:
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  localization_key = cast(str, values["disabled_key"] if flag_enabled else values["enabled_key"])
  localized = run_bounded([*commands["localize"], localization_key], **bounded)
  if localized is None:
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  notification = run_bounded(
    [
      *commands["notify"],
      cast(str, values["notification_glyph"]),
      localized.decode("utf-8", errors="surrogateescape").rstrip("\n"),
    ],
    **bounded,
  )
  if notification is None:
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  return statuses["success"]
