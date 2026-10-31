from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  commands: dict[str, list[str]]
  paths: dict[str, str]
  patterns: dict[str, str]
  udev_touchpad_property: str


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid touchpad configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid touchpad configuration: {label} must be a non-empty string")
  return value


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(
    isinstance(item, str) and item for item in value
  ):
    raise ValueError(f"invalid touchpad configuration: {label} must be a non-empty list of strings")
  return cast(list[str], value)


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-touchpad.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  commands = _mapping(document.get("commands"), "commands")
  paths = _mapping(document.get("paths"), "paths")
  patterns = _mapping(document.get("patterns"), "patterns")
  identifiers = _mapping(document.get("identifiers"), "identifiers")
  return {
    "commands": {
      "hyprland_devices": _strings(commands.get("hyprland_devices"), "commands.hyprland_devices"),
      "mouse_names": _strings(commands.get("mouse_names"), "commands.mouse_names"),
      "udev_properties": _strings(commands.get("udev_properties"), "commands.udev_properties"),
    },
    "paths": {
      "input_class_default": _text(paths.get("input_class_default"), "paths.input_class_default"),
      "input_class_environment": _text(paths.get("input_class_environment"), "paths.input_class_environment"),
      "event_glob": _text(paths.get("event_glob"), "paths.event_glob"),
      "device_name_relative": _text(paths.get("device_name_relative"), "paths.device_name_relative"),
    },
    "patterns": {
      "named_touchpad": _text(patterns.get("named_touchpad"), "patterns.named_touchpad"),
      "name_characters_to_replace": _text(patterns.get("name_characters_to_replace"), "patterns.name_characters_to_replace"),
      "duplicate_name_suffix": _text(patterns.get("duplicate_name_suffix"), "patterns.duplicate_name_suffix"),
    },
    "udev_touchpad_property": _text(identifiers.get("udev_touchpad_property"), "identifiers.udev_touchpad_property"),
  }


def _hyprland_mice(settings: Settings) -> list[str]:
  try:
    devices = subprocess.run(
      settings["commands"]["hyprland_devices"],
      check=False,
      stdout=subprocess.PIPE,
    )
  except OSError:
    return []
  try:
    names = subprocess.run(
      settings["commands"]["mouse_names"],
      input=devices.stdout,
      check=False,
      stdout=subprocess.PIPE,
      text=True,
    )
  except OSError:
    return []
  if not isinstance(names.stdout, str):
    return []
  return cast(list[str], names.stdout.splitlines())


def _named_touchpad(mice: list[str], pattern: re.Pattern[str]) -> str:
  return next((mouse for mouse in mice if pattern.search(mouse)), "")


def _udev_touchpad(settings: Settings, mice: list[str]) -> str:
  paths = settings["paths"]
  patterns = settings["patterns"]
  input_class = Path(os.environ.get(paths["input_class_environment"], paths["input_class_default"]))
  try:
    event_devices = sorted(input_class.glob(paths["event_glob"]))
  except OSError:
    return ""
  name_pattern = re.compile(patterns["name_characters_to_replace"])
  duplicate_pattern = re.compile(patterns["duplicate_name_suffix"])
  relative_name = Path(paths["device_name_relative"])

  for event in event_devices:
    try:
      with (event / relative_name).open(encoding="utf-8") as stream:
        name = stream.read().rstrip("\n").lower()
    except (OSError, UnicodeError):
      continue
    name = name_pattern.sub("-", name)
    matching_mouse = next((
      mouse for mouse in mice
      if mouse == name or (
        mouse.startswith(f"{name}-")
        and duplicate_pattern.fullmatch(mouse[len(name) + 1:]) is not None
      )
    ), "")
    if not matching_mouse:
      continue
    try:
      properties = subprocess.run(
        [*settings["commands"]["udev_properties"], str(event)],
        check=False,
        capture_output=True,
        text=True,
      )
    except OSError:
      continue
    if settings["udev_touchpad_property"] in properties.stdout.splitlines():
      return matching_mouse
  return ""


def touchpad_main() -> int:
  try:
    settings = _settings()
    mice = _hyprland_mice(settings)
    touchpad = _named_touchpad(mice, re.compile(settings["patterns"]["named_touchpad"], re.IGNORECASE))
    if not touchpad:
      touchpad = _udev_touchpad(settings, mice)
  except (KeyError, OSError, UnicodeError, TypeError, ValueError, re.error, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG
  if touchpad:
    print(touchpad)
    return 0
  return 1
