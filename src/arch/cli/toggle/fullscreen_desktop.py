from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import TypedDict, cast

import yaml
from arch.cli.hyprland.toggle import enabled_main as hyprland_enabled_main
from arch.cli.hyprland.toggle import set_main as hyprland_set_main
from arch.cli.toggle.bar import main as bar_main
from arch.cli.toggle.state import is_enabled


class Settings(TypedDict):
  actions: dict[str, str]
  flags: dict[str, str]
  messages: dict[str, str]
  statuses: dict[str, int]


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load(
    (root / "data/cli/fullscreen-desktop-toggle.yml").read_text(encoding="utf-8")
  )
  if not isinstance(raw, dict):
    raise ValueError("invalid fullscreen desktop toggle configuration")
  document = cast(dict[object, object], raw)
  actions_raw = document.get("actions")
  flags_raw = document.get("flags")
  messages_raw = document.get("messages")
  statuses_raw = document.get("statuses")
  if not all(isinstance(section, dict) for section in (actions_raw, flags_raw, messages_raw, statuses_raw)):
    raise ValueError("incomplete fullscreen desktop toggle configuration")
  actions = cast(dict[object, object], actions_raw)
  flags = cast(dict[object, object], flags_raw)
  messages = cast(dict[object, object], messages_raw)
  statuses = cast(dict[object, object], statuses_raw)
  required_actions = ("default", "toggle", "enable", "disable")
  if not all(isinstance(actions.get(name), str) and actions[name] for name in required_actions):
    raise ValueError("incomplete fullscreen desktop toggle actions")
  if not all(isinstance(flags.get(name), str) and flags[name] for name in ("bar", "window_gaps")):
    raise ValueError("incomplete fullscreen desktop toggle flags")
  if not isinstance(messages.get("usage"), str) or not messages["usage"]:
    raise ValueError("missing fullscreen desktop toggle usage")
  if not isinstance(messages.get("state_error"), str) or not messages["state_error"]:
    raise ValueError("missing fullscreen desktop toggle error")
  if any(
    type(statuses.get(name)) is not int or not 0 <= cast(int, statuses[name]) <= 255
    for name in ("invalid_arguments", "configuration_error")
  ):
    raise ValueError("invalid fullscreen desktop toggle status")
  return {
    "actions": {name: cast(str, actions[name]) for name in required_actions},
    "flags": {name: cast(str, flags[name]) for name in ("bar", "window_gaps")},
    "messages": {name: cast(str, messages[name]) for name in ("usage", "state_error")},
    "statuses": {
      name: cast(int, statuses[name]) for name in ("invalid_arguments", "configuration_error")
    },
  }


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return os.EX_CONFIG
  actions = settings["actions"]
  if len(arguments) > 1:
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]
  action = arguments[0] if arguments else actions["default"]
  if action not in {actions["toggle"], actions["enable"], actions["disable"]}:
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]
  flags = settings["flags"]
  try:
    bar_off_enabled = is_enabled(flags["bar"])
    gaps_status = hyprland_enabled_main([flags["window_gaps"]])
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print(settings["messages"]["state_error"], file=sys.stderr)
    return settings["statuses"]["configuration_error"]
  if gaps_status not in {0, 1}:
    return gaps_status
  if action == actions["toggle"]:
    action = actions["disable"] if bar_off_enabled and gaps_status == 0 else actions["enable"]
  bar_status = bar_main([action])
  if bar_status != 0:
    return bar_status
  return hyprland_set_main([flags["window_gaps"], action])
