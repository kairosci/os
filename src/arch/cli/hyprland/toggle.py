from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import TypedDict

import yaml


class Settings(TypedDict):
  state_directory: str
  filename_suffix: str
  source_directory: str
  actions: dict[str, str]
  reload_command: list[str]
  messages: dict[str, str]


def _string_mapping(value: object, label: str) -> dict[str, str]:
  if not isinstance(value, dict) or not all(
    isinstance(key, str) and isinstance(item, str) and item for key, item in value.items()
  ):
    raise ValueError(f"invalid Hyprland toggle {label}")
  return {key: item for key, item in value.items() if isinstance(key, str) and isinstance(item, str)}


def _string_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"invalid Hyprland toggle {label}")
  return [item for item in value if isinstance(item, str)]


def _settings() -> Settings:
  settings_path = Path(os.environ["AP"]) / "data/cli/hyprland-toggle.yml"
  raw = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise ValueError("invalid Hyprland toggle configuration")
  state_directory = raw.get("home_relative_state_directory")
  filename_suffix = raw.get("filename_suffix")
  source_directory = raw.get("source_directory")
  actions = _string_mapping(raw.get("actions"), "actions")
  commands = raw.get("commands")
  messages = _string_mapping(raw.get("messages"), "messages")
  if (
    not isinstance(state_directory, str)
    or not state_directory
    or Path(state_directory).is_absolute()
    or ".." in Path(state_directory).parts
  ):
    raise ValueError("invalid Hyprland toggle state directory")
  if not isinstance(filename_suffix, str) or not filename_suffix or "/" in filename_suffix or "\\" in filename_suffix:
    raise ValueError("invalid Hyprland toggle filename suffix")
  if (
    not isinstance(source_directory, str)
    or not source_directory
    or Path(source_directory).is_absolute()
    or ".." in Path(source_directory).parts
  ):
    raise ValueError("invalid Hyprland toggle source directory")
  if not {"enable", "disable", "toggle", "enabled_output", "disabled_output"} <= set(actions):
    raise ValueError("incomplete Hyprland toggle actions")
  if not isinstance(commands, dict):
    raise ValueError("invalid Hyprland toggle commands")
  reload_command = _string_list(commands.get("reload"), "reload command")
  if not {"usage", "query_usage", "missing_flag", "read_error", "state_error"} <= set(messages):
    raise ValueError("incomplete Hyprland toggle messages")
  return {
    "state_directory": state_directory,
    "filename_suffix": filename_suffix,
    "source_directory": source_directory,
    "actions": actions,
    "reload_command": reload_command,
    "messages": messages,
  }


def _toggle_path(name: str, settings: Settings) -> Path:
  if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
    raise ValueError("toggle name must be a plain filename stem")
  return Path(os.environ["HOME"]) / settings["state_directory"] / f"{name}{settings['filename_suffix']}"


def _enable(path: Path, source: Path) -> bool:
  if not source.is_file():
    return False
  path.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(prefix=".hyprland-toggle-", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as target, source.open("rb") as original:
      shutil.copyfileobj(original, target)
      target.flush()
      os.fsync(target.fileno())
    os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
    os.replace(temporary, path)
  finally:
    temporary.unlink(missing_ok=True)
  return True


def _main(args: list[str], enabled: bool) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not load Hyprland toggle configuration", file=sys.stderr)
    return os.EX_CONFIG
  if len(args) != 1:
    print(settings["messages"]["query_usage"], file=sys.stderr)
    return 2
  try:
    path = _toggle_path(args[0], settings)
    try:
      mode = path.stat().st_mode
      exists = stat.S_ISREG(mode)
    except FileNotFoundError:
      exists = False
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print(settings["messages"]["read_error"], file=sys.stderr)
    return os.EX_CONFIG
  return 0 if exists == enabled else 1


def set_main(args: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not load Hyprland toggle configuration", file=sys.stderr)
    return os.EX_CONFIG
  if not 1 <= len(args) <= 2:
    print(settings["messages"]["usage"], file=sys.stderr)
    return 2

  name = args[0]
  actions = settings["actions"]
  action = args[1] if len(args) == 2 else actions["toggle"]
  if action not in {actions["enable"], actions["disable"], actions["toggle"]}:
    print(settings["messages"]["usage"], file=sys.stderr)
    return 2
  report_status = action == actions["toggle"]

  try:
    path = _toggle_path(name, settings)
    try:
      is_enabled = stat.S_ISREG(path.stat().st_mode)
    except FileNotFoundError:
      is_enabled = False
    if action == actions["toggle"]:
      action = actions["disable"] if is_enabled else actions["enable"]
    if action == actions["enable"]:
      source = Path(os.environ["AP"]) / settings["source_directory"] / f"{name}{settings['filename_suffix']}"
      if not _enable(path, source):
        print(settings["messages"]["missing_flag"].format(name=name), file=sys.stderr)
        return 1
      if report_status:
        print(settings["actions"]["enabled_output"])
    else:
      path.unlink(missing_ok=True)
      if report_status:
        print(settings["actions"]["disabled_output"])
    result = subprocess.run(settings["reload_command"], check=False, stdout=subprocess.DEVNULL)
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print(settings["messages"]["state_error"], file=sys.stderr)
    return os.EX_CANTCREAT
  return result.returncode


def enabled_main(args: list[str]) -> int:
  return _main(args, True)


def disabled_main(args: list[str]) -> int:
  return _main(args, False)
