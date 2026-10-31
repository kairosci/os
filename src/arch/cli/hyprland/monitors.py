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


class AppleCommand(TypedDict):
  name_field: str
  focused_field: str
  focused_value: object
  make_field: str
  make: str
  model_field: str
  model_pattern: str


class ModelessCommand(TypedDict):
  disabled_field: str
  disabled_value: object
  dimension_fields: list[str]
  no_mode_value: int
  modeless_status: int
  working_status: int
  unknown_status: int


class ExternalActiveCommand(TypedDict):
  disabled_field: str
  active_value: object
  active_status: int
  inactive_status: int


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
  apple: AppleCommand
  modeless: ModelessCommand
  external_active: ExternalActiveCommand
  output_field: str
  query_timeout_seconds: int
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


def _apple_command(value: object) -> AppleCommand:
  command = _mapping(value, "apple")
  model_pattern = _text(command.get("model_pattern"), "apple.model_pattern")
  try:
    re.compile(model_pattern)
  except re.error as error:
    raise ValueError("invalid Hyprland monitor configuration: apple.model_pattern is invalid") from error
  return {
    "name_field": _text(command.get("name_field"), "apple.name_field"),
    "focused_field": _text(command.get("focused_field"), "apple.focused_field"),
    "focused_value": command.get("focused_value"),
    "make_field": _text(command.get("make_field"), "apple.make_field"),
    "make": _text(command.get("make"), "apple.make"),
    "model_field": _text(command.get("model_field"), "apple.model_field"),
    "model_pattern": model_pattern,
  }


def _modeless_command(value: object) -> ModelessCommand:
  command = _mapping(value, "modeless")
  fields = _mapping(command.get("fields"), "modeless.fields")
  statuses = _mapping(command.get("statuses"), "modeless.statuses")
  return {
    "disabled_field": _text(fields.get("disabled"), "modeless.fields.disabled"),
    "disabled_value": fields.get("disabled_value"),
    "dimension_fields": _command(fields.get("dimensions"), "modeless.fields.dimensions"),
    "no_mode_value": _integer(fields.get("no_mode_value"), "modeless.fields.no_mode_value"),
    "modeless_status": _integer(statuses.get("modeless"), "modeless.statuses.modeless"),
    "working_status": _integer(statuses.get("working"), "modeless.statuses.working"),
    "unknown_status": _integer(statuses.get("unknown"), "modeless.statuses.unknown"),
  }


def _external_active_command(value: object) -> ExternalActiveCommand:
  command = _mapping(value, "external_active")
  fields = _mapping(command.get("fields"), "external_active.fields")
  statuses = _mapping(command.get("statuses"), "external_active.statuses")
  return {
    "disabled_field": _text(fields.get("disabled"), "external_active.fields.disabled"),
    "active_value": fields.get("active_value"),
    "active_status": _integer(statuses.get("active"), "external_active.statuses.active"),
    "inactive_status": _integer(statuses.get("inactive"), "external_active.statuses.inactive"),
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
  query_timeout_seconds = _integer(settings.get("query_timeout_seconds"), "query_timeout_seconds")
  if query_timeout_seconds <= 0:
    raise ValueError("invalid Hyprland monitor configuration: query_timeout_seconds must be positive")
  return {
    "commands": {
      "focused": _focused_command(commands.get("focused")),
      "laptop": _laptop_command(commands.get("laptop")),
    },
    "apple": _apple_command(settings.get("apple")),
    "modeless": _modeless_command(settings.get("modeless")),
    "external_active": _external_active_command(settings.get("external_active")),
    "output_field": _text(settings.get("output_field"), "output_field"),
    "query_timeout_seconds": query_timeout_seconds,
    "exit_codes": {
      "invalid_json": {
        "focused": _integer(invalid_json.get("focused"), "exit_codes.invalid_json.focused"),
        "laptop": _integer(invalid_json.get("laptop"), "exit_codes.invalid_json.laptop"),
      },
    },
  }


def _monitors(settings: Settings, command: Literal["focused", "laptop"]) -> list[object] | None:
  result = subprocess.run(
    settings["commands"][command]["command"],
    check=False,
    capture_output=True,
    text=True,
    timeout=settings["query_timeout_seconds"],
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


def _apple_main(arguments: list[str]) -> int:
  settings = _settings()
  apple = settings["apple"]
  try:
    monitors = _monitors(settings, "focused")
  except json.JSONDecodeError:
    return settings["exit_codes"]["invalid_json"]["focused"]
  if monitors is None:
    return settings["exit_codes"]["invalid_json"]["focused"]
  pattern = re.compile(apple["model_pattern"])
  named_monitor = arguments[0] if arguments else ""
  for monitor in monitors:
    if not isinstance(monitor, dict):
      continue
    selected = (
      monitor.get(apple["name_field"]) == named_monitor
      if named_monitor
      else monitor.get(apple["focused_field"]) == apple["focused_value"]
    )
    model = monitor.get(apple["model_field"])
    if selected and monitor.get(apple["make_field"]) == apple["make"] and isinstance(model, str) and pattern.search(model):
      return 0
  return 1


def apple_main(arguments: list[str]) -> int:
  return _entry(lambda: _apple_main(arguments), "Apple")


def _modeless_main() -> int:
  settings = _settings()
  command = settings["modeless"]
  try:
    result = subprocess.run(
      settings["commands"]["laptop"]["command"],
      check=False,
      capture_output=True,
      text=True,
      timeout=settings["query_timeout_seconds"],
    )
  except (OSError, subprocess.SubprocessError):
    return command["unknown_status"]
  if result.returncode != 0 or not result.stdout:
    return command["unknown_status"]
  try:
    monitors: object = json.loads(result.stdout)
  except json.JSONDecodeError:
    return command["unknown_status"]
  if not isinstance(monitors, list):
    return command["unknown_status"]
  for monitor in monitors:
    if not isinstance(monitor, dict) or monitor.get(command["disabled_field"]) == command["disabled_value"]:
      continue
    for dimension in command["dimension_fields"]:
      value = monitor.get(dimension)
      if isinstance(value, (int, float)) and not isinstance(value, bool) and value == command["no_mode_value"]:
        return command["modeless_status"]
  return command["working_status"]


def modeless_main() -> int:
  return _entry(_modeless_main, "modeless")


def _external_active_main() -> int:
  settings = _settings()
  external_active = settings["external_active"]
  try:
    monitors = _monitors(settings, "laptop")
  except json.JSONDecodeError:
    return external_active["inactive_status"]
  if monitors is None:
    return external_active["inactive_status"]
  internal_name = re.compile(settings["commands"]["laptop"]["name_pattern"])
  for monitor in monitors:
    if not isinstance(monitor, dict):
      continue
    name = monitor.get(settings["output_field"])
    if (
      isinstance(name, str)
      and not internal_name.search(name)
      and monitor.get(external_active["disabled_field"]) == external_active["active_value"]
    ):
      return external_active["active_status"]
  return external_active["inactive_status"]


def external_active_main() -> int:
  return _entry(_external_active_main, "external monitor")
