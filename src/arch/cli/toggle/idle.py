from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import stat
import sys
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  state_file: PurePosixPath
  actions: dict[str, list[str]]
  outputs: dict[str, str]
  messages: dict[str, str]
  statuses: dict[str, int]


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/idle-toggle.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise ValueError("invalid idle toggle configuration")
  document = cast(dict[object, object], raw)
  state_file = document.get("state_file")
  if not isinstance(state_file, str):
    raise ValueError("invalid idle toggle state path")
  state_path = PurePosixPath(state_file)
  if state_path.is_absolute() or not state_path.parts or any(
    part in {"", ".", ".."} for part in state_file.split("/")
  ):
    raise ValueError("invalid idle toggle state path")
  actions_raw = document.get("actions")
  if not isinstance(actions_raw, dict):
    raise ValueError("invalid idle toggle actions")
  actions = cast(dict[object, object], actions_raw)
  parsed_actions: dict[str, list[str]] = {}
  action_values: set[str] = set()
  for name in ("toggle", "stay_awake", "allow_idle", "status", "enabled", "state_path"):
    values = actions.get(name)
    if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
      raise ValueError(f"invalid idle toggle action: {name}")
    parsed_actions[name] = cast(list[str], values)
    if action_values.intersection(parsed_actions[name]):
      raise ValueError("duplicate idle toggle action")
    action_values.update(parsed_actions[name])
  outputs_raw = document.get("outputs")
  messages_raw = document.get("messages")
  statuses_raw = document.get("statuses")
  if not isinstance(outputs_raw, dict) or not isinstance(messages_raw, dict) or not isinstance(statuses_raw, dict):
    raise ValueError("incomplete idle toggle configuration")
  outputs = cast(dict[object, object], outputs_raw)
  messages = cast(dict[object, object], messages_raw)
  statuses = cast(dict[object, object], statuses_raw)
  required_outputs = ("stay_awake_idle_state", "allow_idle_idle_state", "stay_awake_status", "allow_idle_status")
  if not all(isinstance(outputs.get(name), str) and outputs[name] for name in required_outputs):
    raise ValueError("incomplete idle toggle output configuration")
  required_messages = ("usage", "state_error")
  if not all(isinstance(messages.get(name), str) and messages[name] for name in required_messages):
    raise ValueError("incomplete idle toggle message configuration")
  required_statuses = ("invalid_arguments", "state_error", "stay_awake_enabled", "stay_awake_disabled")
  if not all(type(statuses.get(name)) is int and 0 <= cast(int, statuses[name]) <= 255 for name in required_statuses):
    raise ValueError("invalid idle toggle status configuration")
  return {
    "state_file": state_path,
    "actions": parsed_actions,
    "outputs": {name: cast(str, outputs[name]) for name in required_outputs},
    "messages": {name: cast(str, messages[name]) for name in required_messages},
    "statuses": {name: cast(int, statuses[name]) for name in required_statuses},
  }


def _state_parent(state_path: PurePosixPath, create: bool) -> tuple[int, str] | None:
  home = Path.home().resolve(strict=True)
  flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
  descriptor = os.open(home, flags)
  try:
    for component in state_path.parts[:-1]:
      try:
        child = os.open(component, flags, dir_fd=descriptor)
      except FileNotFoundError:
        if not create:
          os.close(descriptor)
          return None
        try:
          os.mkdir(component, 0o700, dir_fd=descriptor)
        except FileExistsError:
          pass
        child = os.open(component, flags, dir_fd=descriptor)
      os.close(descriptor)
      descriptor = child
    return descriptor, state_path.parts[-1]
  except BaseException:
    os.close(descriptor)
    raise


def _enabled(state_path: PurePosixPath) -> bool:
  parent = _state_parent(state_path, create=False)
  if parent is None:
    return False
  descriptor, name = parent
  try:
    try:
      return stat.S_ISREG(os.stat(name, dir_fd=descriptor, follow_symlinks=False).st_mode)
    except FileNotFoundError:
      return False
  finally:
    os.close(descriptor)


def _set_enabled(state_path: PurePosixPath, enabled: bool) -> None:
  parent = _state_parent(state_path, create=enabled)
  if parent is None:
    return
  descriptor, name = parent
  try:
    if enabled:
      flags = os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
      state_descriptor = os.open(name, flags, 0o600, dir_fd=descriptor)
      try:
        if not stat.S_ISREG(os.fstat(state_descriptor).st_mode):
          raise OSError("state path is not a regular file")
      finally:
        os.close(state_descriptor)
    else:
      try:
        os.unlink(name, dir_fd=descriptor)
      except FileNotFoundError:
        pass
  finally:
    os.close(descriptor)


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return os.EX_CONFIG
  actions = settings["actions"]
  outputs = settings["outputs"]
  messages = settings["messages"]
  statuses = settings["statuses"]
  if len(arguments) > 1:
    print(messages["usage"], file=sys.stderr)
    return statuses["invalid_arguments"]
  action = arguments[0] if arguments else actions["toggle"][0]
  action_name = next((name for name, values in actions.items() if action in values), None)
  if action_name is None:
    print(messages["usage"], file=sys.stderr)
    return statuses["invalid_arguments"]
  state_path = settings["state_file"]
  if action_name == "state_path":
    try:
      home = Path.home().resolve(strict=True)
      parent = _state_parent(state_path, create=False)
      if parent is not None:
        os.close(parent[0])
      print(home.joinpath(*state_path.parts))
      return 0
    except OSError:
      print(messages["state_error"], file=sys.stderr)
      return statuses["state_error"]
  try:
    enabled = _enabled(state_path)
    if action_name == "status":
      print(outputs["stay_awake_status"] if enabled else outputs["allow_idle_status"])
      return 0
    if action_name == "enabled":
      key = "stay_awake_enabled" if enabled else "stay_awake_disabled"
      return statuses[key]
    if action_name == "toggle":
      enabled = not enabled
    elif action_name == "stay_awake":
      enabled = True
    elif action_name == "allow_idle":
      enabled = False
    _set_enabled(state_path, enabled)
  except (OSError, RuntimeError, ValueError):
    print(messages["state_error"], file=sys.stderr)
    return statuses["state_error"]
  output = "stay_awake_idle_state" if enabled else "allow_idle_idle_state"
  print(outputs[output])
  return 0
