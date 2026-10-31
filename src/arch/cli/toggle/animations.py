from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import yaml
from arch.cli.lib.bounded import run_bounded


def _settings() -> dict[str, object]:
  root = Path(os.environ["AP"])
  document: object = yaml.safe_load((root / "data/cli/animations-toggle.yml").read_text(encoding="utf-8"))
  if not isinstance(document, dict):
    raise ValueError("invalid animations toggle configuration")
  commands = document.get("commands")
  values = document.get("values")
  limits = document.get("limits")
  messages = document.get("messages")
  statuses = document.get("statuses")
  if not all(isinstance(section, dict) for section in (commands, values, limits, messages, statuses)):
    raise ValueError("incomplete animations toggle configuration")
  commands = cast(dict[str, object], commands)
  values = cast(dict[str, object], values)
  limits = cast(dict[str, object], limits)
  messages = cast(dict[str, object], messages)
  statuses = cast(dict[str, object], statuses)
  actions = values.get("actions")
  keys = values.get("notification_keys")
  if not isinstance(actions, dict) or not isinstance(keys, dict):
    raise ValueError("incomplete animations toggle values")
  result: dict[str, object] = {
    "actions": {
      key: actions.get(key)
      for key in ("toggle", "enable", "disable", "animations_on", "animations_off", "accepted")
    },
    "keys": {key: keys.get(key) for key in ("enabled", "disabled")},
    "flag_enabled_output": values.get("flag_enabled_output"),
    "glyph": values.get("notification_glyph"),
    "messages": {key: messages.get(key) for key in ("usage", "command_error")},
    "statuses": {key: statuses.get(key) for key in ("success", "invalid_arguments", "command_error")},
    "limits": {key: limits.get(key) for key in (
      "command_timeout_seconds", "cleanup_timeout_seconds", "maximum_output_bytes", "read_chunk_bytes"
    )},
  }
  result["commands"] = {}
  parsed_commands = cast(dict[str, list[str]], result["commands"])
  for key in ("set_flag", "localize", "notify"):
    command = commands.get(key)
    if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
      raise ValueError(f"invalid animations command: {key}")
    parsed_commands[key] = cast(list[str], command)
  for section, names in (("actions", ("toggle", "enable", "disable", "animations_on", "animations_off")),
                         ("keys", ("enabled", "disabled")),
                         ("messages", ("usage", "command_error"))):
    mapping = cast(dict[str, object], result[section])
    if not all(isinstance(mapping[name], str) and mapping[name] for name in names):
      raise ValueError(f"incomplete animations {section}")
  if not isinstance(result["glyph"], str) or not result["glyph"] or not isinstance(result["flag_enabled_output"], str):
    raise ValueError("invalid animations notification configuration")
  accepted = cast(dict[str, object], result["actions"]).get("accepted")
  if not isinstance(accepted, list) or not accepted or not all(isinstance(action, str) for action in accepted):
    raise ValueError("invalid animations actions")
  for name, value in cast(dict[str, object], result["limits"]).items():
    if type(value) is not int or value <= 0:
      raise ValueError(f"invalid animations limit: {name}")
  for name, value in cast(dict[str, object], result["statuses"]).items():
    if type(value) is not int or not 0 <= value <= 255:
      raise ValueError(f"invalid animations status: {name}")
  return result


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not load animations toggle configuration", file=sys.stderr)
    return os.EX_CONFIG
  actions = cast(dict[str, object], settings["actions"])
  messages = cast(dict[str, str], settings["messages"])
  statuses = cast(dict[str, int], settings["statuses"])
  accepted = cast(list[str], actions["accepted"])
  if len(arguments) > 1 or (arguments and arguments[0] not in accepted):
    print(messages["usage"], file=sys.stderr)
    return statuses["invalid_arguments"]
  requested = arguments[0] if arguments else actions["toggle"]
  flag_action = cast(str, (
    actions["animations_on"] if requested == actions["enable"]
    else actions["animations_off"] if requested == actions["disable"]
    else actions["toggle"]
  ))
  commands = cast(dict[str, list[str]], settings["commands"])
  limits = cast(dict[str, int], settings["limits"])
  timeout = limits["command_timeout_seconds"]
  cleanup = limits["cleanup_timeout_seconds"]
  maximum = limits["maximum_output_bytes"]
  chunk = limits["read_chunk_bytes"]
  output = run_bounded(
    [*commands["set_flag"], flag_action], timeout_seconds=timeout,
    cleanup_timeout_seconds=cleanup, max_output_bytes=maximum, read_chunk_bytes=chunk,
  )
  if output is None:
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  if requested == actions["toggle"]:
    try:
      flag_enabled = output.decode("ascii", errors="strict").strip() == settings["flag_enabled_output"]
    except UnicodeError:
      print(messages["command_error"], file=sys.stderr)
      return statuses["command_error"]
    animations_enabled = not flag_enabled
  else:
    animations_enabled = requested == actions["enable"]
  keys = cast(dict[str, str], settings["keys"])
  key = keys["enabled"] if animations_enabled else keys["disabled"]
  localized = run_bounded(
    [*commands["localize"], key], timeout_seconds=timeout,
    cleanup_timeout_seconds=cleanup, max_output_bytes=maximum, read_chunk_bytes=chunk,
  )
  if localized is None:
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  notification = run_bounded(
    [*commands["notify"], cast(str, settings["glyph"]), localized.decode("utf-8", errors="surrogateescape").rstrip("\n")],
    timeout_seconds=timeout, cleanup_timeout_seconds=cleanup,
    max_output_bytes=maximum, read_chunk_bytes=chunk,
  )
  if notification is None:
    print(messages["command_error"], file=sys.stderr)
    return statuses["command_error"]
  return cast(int, statuses["success"])
