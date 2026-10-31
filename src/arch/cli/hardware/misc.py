from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import TypedDict

import yaml


class Settings(TypedDict):
  commands: dict[str, list[str]]
  paths: dict[str, str]
  patterns: dict[str, str]
  fields: dict[str, str]
  monitor_status: dict[str, str]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid hardware configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid hardware configuration: {label} must be a non-empty string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"invalid hardware configuration: {label} must be a non-empty list of strings")
  return [item for item in value if isinstance(item, str)]


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-misc.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  commands = _mapping(document.get("commands"), "commands")
  paths = _mapping(document.get("paths"), "paths")
  patterns = _mapping(document.get("patterns"), "patterns")
  fields = _mapping(document.get("fields"), "fields")
  monitor_status = _mapping(document.get("monitor_status"), "monitor_status")
  return {
    "commands": {"hyprland_devices": _text_list(commands.get("hyprland_devices"), "commands.hyprland_devices")},
    "paths": {"vulkan_icd_directory": _text(paths.get("vulkan_icd_directory"), "paths.vulkan_icd_directory")},
    "patterns": {"vulkan_icd": _text(patterns.get("vulkan_icd"), "patterns.vulkan_icd")},
    "fields": {
      "touch": _text(fields.get("touch"), "fields.touch"),
      "tablets": _text(fields.get("tablets"), "fields.tablets"),
      "name": _text(fields.get("name"), "fields.name"),
    },
    "monitor_status": {
      "directory_environment": _text(monitor_status.get("directory_environment"), "monitor_status.directory_environment"),
      "default_directory": _text(monitor_status.get("default_directory"), "monitor_status.default_directory"),
      "status_glob": _text(monitor_status.get("status_glob"), "monitor_status.status_glob"),
      "internal_connector_pattern": _text(monitor_status.get("internal_connector_pattern"), "monitor_status.internal_connector_pattern"),
      "connected_value": _text(monitor_status.get("connected_value"), "monitor_status.connected_value"),
    },
  }


def _touchscreen_name(settings: Settings) -> str:
  result = subprocess.run(settings["commands"]["hyprland_devices"], check=False, capture_output=True, text=True)
  try:
    devices: object = json.loads(result.stdout)
  except ValueError:
    return ""
  if not isinstance(devices, dict):
    return ""
  for category in (settings["fields"]["touch"], settings["fields"]["tablets"]):
    items = devices.get(category)
    if not isinstance(items, list) or not items:
      continue
    first = items[0]
    if not isinstance(first, dict):
      return ""
    name = first.get(settings["fields"]["name"])
    if isinstance(name, str):
      return name
    if isinstance(name, (int, float)):
      return str(name)
    return ""
  return ""


def touchscreen_main() -> int:
  try:
    settings = _settings()
    name = _touchscreen_name(settings)
  except (KeyError, OSError, UnicodeError, TypeError, ValueError, subprocess.SubprocessError, yaml.YAMLError) as error:
    print(f"Could not detect a touchscreen: {error}", file=sys.stderr)
    return os.EX_CONFIG
  if name:
    print(name)
    return 0
  return 1


def vulkan_main() -> int:
  try:
    settings = _settings()
    directory = Path(settings["paths"]["vulkan_icd_directory"])
    return 0 if directory.is_dir() and next(directory.glob(settings["patterns"]["vulkan_icd"]), None) else 1
  except (KeyError, OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not detect Vulkan configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG


def external_monitors_main() -> int:
  try:
    settings = _settings()["monitor_status"]
    directory = Path(os.environ.get(settings["directory_environment"], settings["default_directory"]))
    internal_connector = re.compile(settings["internal_connector_pattern"])
    for status in directory.glob(settings["status_glob"]):
      if not status.exists() or internal_connector.search(status.parent.name):
        continue
      try:
        connected = status.read_text(encoding="utf-8").rstrip("\n")
      except OSError:
        continue
      if connected == settings["connected_value"]:
        return 0
    return 1
  except (KeyError, OSError, UnicodeError, TypeError, ValueError, re.error, yaml.YAMLError) as error:
    print(f"Could not detect external monitors: {error}", file=sys.stderr)
    return os.EX_CONFIG
