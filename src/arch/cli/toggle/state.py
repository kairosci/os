from __future__ import annotations

import os
from pathlib import Path
import stat
import sys
from typing import TypedDict

import yaml


class Settings(TypedDict):
  state_directory: str
  actions: dict[str, str]
  usage: str
  state_error: str


def _settings() -> Settings:
  settings_path = Path(os.environ["AP"]) / "data/cli/toggle-state.yml"
  raw = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise ValueError("invalid toggle state configuration")
  directory = raw.get("home_relative_state_directory")
  actions = raw.get("actions")
  messages = raw.get("messages")
  if not isinstance(directory, str) or not directory or Path(directory).is_absolute() or ".." in Path(directory).parts:
    raise ValueError("invalid toggle state directory")
  if not isinstance(actions, dict) or not all(isinstance(value, str) and value for value in actions.values()):
    raise ValueError("invalid toggle state actions")
  if not {"enable", "disable", "toggle"} <= set(actions):
    raise ValueError("incomplete toggle state actions")
  if not isinstance(messages, dict):
    raise ValueError("invalid toggle state messages")
  usage = messages.get("usage")
  state_error = messages.get("state_error")
  if not isinstance(usage, str) or not usage or not isinstance(state_error, str) or not state_error:
    raise ValueError("incomplete toggle state messages")
  return {"state_directory": directory, "actions": actions, "usage": usage, "state_error": state_error}


def _state_path(name: str, settings: Settings) -> Path:
  parts = name.split("/")
  if not name or any(part in {"", ".", ".."} for part in parts):
    raise ValueError("toggle name must be a relative path without traversal components")
  return Path(os.environ["HOME"]) / settings["state_directory"] / name


def enabled_main(args: list[str]) -> int:
  if not args:
    return 1
  try:
    settings = _settings()
    return 0 if _state_path(args[0], settings).is_file() else 1
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not read toggle state", file=sys.stderr)
    return os.EX_CONFIG


def set_main(args: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not load toggle state configuration", file=sys.stderr)
    return os.EX_CONFIG
  if not args:
    print(settings["usage"], file=sys.stderr)
    return 1

  actions = settings["actions"]
  action = args[1] if len(args) > 1 and args[1] else actions["toggle"]
  if action not in {actions["enable"], actions["disable"], actions["toggle"]}:
    print(settings["usage"], file=sys.stderr)
    return 1

  try:
    path = _state_path(args[0], settings)
    try:
      enabled = stat.S_ISREG(path.stat().st_mode)
    except FileNotFoundError:
      enabled = False
    if action == actions["toggle"]:
      action = actions["disable"] if enabled else actions["enable"]
    if action == actions["enable"]:
      path.parent.mkdir(parents=True, exist_ok=True)
      path.touch(exist_ok=True)
    else:
      path.unlink(missing_ok=True)
  except (KeyError, OSError, TypeError, ValueError):
    print(settings["state_error"], file=sys.stderr)
    return os.EX_CANTCREAT
  return 0
