from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Literal, TypedDict

import yaml


class FocusedCommand(TypedDict):
  command: list[str]
  selected_field: str
  selected_value: object


class LaptopCommand(TypedDict):
  command: list[str]
  name_pattern: str
  first_match: bool


class Commands(TypedDict):
  focused: FocusedCommand
  laptop: LaptopCommand


class InvalidJsonExitCodes(TypedDict):
  focused: int
  laptop: int


class ExitCodes(TypedDict):
  invalid_json: InvalidJsonExitCodes


class Settings(TypedDict):
  commands: Commands
  output_field: str
  exit_codes: ExitCodes


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid Hyprland monitor configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid Hyprland monitor configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid Hyprland monitor configuration: {label} must be an integer")
  return value


def _command(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value:
    raise TypeError(f"invalid Hyprland monitor configuration: {label} must be a non-empty command list")
  command: list[str] = []
  for item in value:
    command.append(_text(item, f"{label} argument"))
  return command


def _focused_command(value: object) -> FocusedCommand:
  command = _mapping(value, "commands.focused")
  return {
    "command": _command(command.get("command"), "commands.focused.command"),
    "selected_field": _text(command.get("selected_field"), "commands.focused.selected_field"),
    "selected_value": command.get("selected_value"),
  }


def _laptop_command(value: object) -> LaptopCommand:
  command = _mapping(value, "commands.laptop")
  name_pattern = _text(command.get("name_pattern"), "commands.laptop.name_pattern")
  try:
    re.compile(name_pattern)
  except re.error as error:
    raise ValueError("invalid Hyprland monitor configuration: commands.laptop.name_pattern is invalid") from error
  first_match = command.get("first_match")
  if not isinstance(first_match, bool):
    raise TypeError("invalid Hyprland monitor configuration: commands.laptop.first_match must be a boolean")
  return {
    "command": _command(command.get("command"), "commands.laptop.command"),
    "name_pattern": name_pattern,
    "first_match": first_match,
  }


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load(
    (root / "data/cli/hyprland-monitors.yml").read_text(encoding="utf-8")
  )
  settings = _mapping(raw, "root")
  commands = _mapping(settings.get("commands"), "commands")
  exit_codes = _mapping(settings.get("exit_codes"), "exit_codes")
  invalid_json = _mapping(exit_codes.get("invalid_json"), "exit_codes.invalid_json")
  return {
    "commands": {
      "focused": _focused_command(commands.get("focused")),
      "laptop": _laptop_command(commands.get("laptop")),
    },
    "output_field": _text(settings.get("output_field"), "output_field"),
    "exit_codes": {
      "invalid_json": {
        "focused": _integer(invalid_json.get("focused"), "exit_codes.invalid_json.focused"),
        "laptop": _integer(invalid_json.get("laptop"), "exit_codes.invalid_json.laptop"),
      },
    },
  }


def _monitors(settings: Settings, command: Literal["focused", "laptop"]) -> list[object] | None:
  result = subprocess.run(
    settings["commands"][command]["command"], check=False, capture_output=True, text=True
  )
  if not result.stdout:
    return None
  monitors: object = json.loads(result.stdout)
  if not isinstance(monitors, list):
    return []
  return [monitor for monitor in monitors]


def _focused_main() -> int:
  settings = _settings()
  command = settings["commands"]["focused"]
  try:
    monitors = _monitors(settings, "focused")
  except json.JSONDecodeError:
    return settings["exit_codes"]["invalid_json"]["focused"]
  if monitors is None:
    return 0
  for monitor in monitors:
    if isinstance(monitor, dict) and monitor.get(command["selected_field"]) == command["selected_value"]:
      print(monitor.get(settings["output_field"]))
  return 0


def _laptop_main() -> int:
  settings = _settings()
  command = settings["commands"]["laptop"]
  try:
    monitors = _monitors(settings, "laptop")
  except json.JSONDecodeError:
    return settings["exit_codes"]["invalid_json"]["laptop"]
  if monitors is None:
    return 0
  pattern = re.compile(command["name_pattern"])
  for monitor in monitors:
    name = monitor.get(settings["output_field"]) if isinstance(monitor, dict) else None
    if isinstance(name, str) and pattern.search(name):
      print(name)
      if command["first_match"]:
        break
  return 0


def _entry(operation: Callable[[], int], label: str) -> int:
  try:
    return operation()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load {label} monitor configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  except subprocess.SubprocessError as error:
    print(f"Could not query {label} monitor: {error}", file=sys.stderr)
    return os.EX_SOFTWARE


def focused_main() -> int:
  return _entry(_focused_main, "focused")


def laptop_main() -> int:
  return _entry(_laptop_main, "laptop")
