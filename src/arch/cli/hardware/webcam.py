from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml

from arch.cli.lib.bounded import run_bounded


class Commands(TypedDict):
  list_devices: list[str]
  device_info: list[str]


class Parsing(TypedDict):
  video_node_pattern: str
  device_caps_marker: str
  capture_capability_prefix: str


class Limits(TypedDict):
  command_timeout_seconds: int
  cleanup_timeout_seconds: int
  maximum_list_output_bytes: int
  maximum_device_info_output_bytes: int
  read_chunk_bytes: int


class Settings(TypedDict):
  commands: Commands
  parsing: Parsing
  limits: Limits
  output: dict[str, str]
  statuses: dict[str, int]


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"invalid webcam configuration: {label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"invalid webcam configuration: {label} must be non-empty text")
  return value


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise TypeError(f"invalid webcam configuration: {label} must be a non-empty string list")
  return cast(list[str], value)


def _positive_integer(value: object, label: str) -> int:
  if type(value) is not int or value <= 0:
    raise TypeError(f"invalid webcam configuration: {label} must be a positive integer")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/webcam.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  raw_commands = _mapping(document.get("commands"), "commands")
  raw_parsing = _mapping(document.get("parsing"), "parsing")
  raw_limits = _mapping(document.get("limits"), "limits")
  raw_output = _mapping(document.get("output"), "output")
  raw_statuses = _mapping(document.get("statuses"), "statuses")
  commands: Commands = {
    "list_devices": _strings(raw_commands.get("list_devices"), "commands.list_devices"),
    "device_info": _strings(raw_commands.get("device_info"), "commands.device_info"),
  }
  if sum(part.count("{device}") for part in commands["device_info"]) != 1:
    raise ValueError("invalid webcam configuration: commands.device_info must contain one device placeholder")
  parsing: Parsing = {
    "video_node_pattern": _text(raw_parsing.get("video_node_pattern"), "parsing.video_node_pattern"),
    "device_caps_marker": _text(raw_parsing.get("device_caps_marker"), "parsing.device_caps_marker"),
    "capture_capability_prefix": _text(
      raw_parsing.get("capture_capability_prefix"), "parsing.capture_capability_prefix"
    ),
  }
  re.compile(parsing["video_node_pattern"])
  limits: Limits = {
    "command_timeout_seconds": _positive_integer(
      raw_limits.get("command_timeout_seconds"), "limits.command_timeout_seconds"
    ),
    "cleanup_timeout_seconds": _positive_integer(
      raw_limits.get("cleanup_timeout_seconds"), "limits.cleanup_timeout_seconds"
    ),
    "maximum_list_output_bytes": _positive_integer(
      raw_limits.get("maximum_list_output_bytes"), "limits.maximum_list_output_bytes"
    ),
    "maximum_device_info_output_bytes": _positive_integer(
      raw_limits.get("maximum_device_info_output_bytes"), "limits.maximum_device_info_output_bytes"
    ),
    "read_chunk_bytes": _positive_integer(raw_limits.get("read_chunk_bytes"), "limits.read_chunk_bytes"),
  }
  output = {
    "separator": _text(raw_output.get("separator"), "output.separator"),
    "trailing_newline": _text(raw_output.get("trailing_newline"), "output.trailing_newline"),
  }
  statuses = {
    key: value
    for key, value in raw_statuses.items()
    if type(value) is int and 0 <= value <= 255
  }
  if set(statuses) != {"list_success", "detected", "absent"} or statuses["list_success"] != 0:
    raise ValueError("invalid webcam configuration: statuses must define list, detected, and absent results")
  if statuses["detected"] != 0 or statuses["absent"] == 0:
    raise ValueError("invalid webcam configuration: device detection statuses are inconsistent")
  return {
    "commands": commands,
    "parsing": parsing,
    "limits": limits,
    "output": output,
    "statuses": statuses,
  }


def _bounded_output(command: list[str], maximum_output_bytes: int, settings: Settings) -> bytes | None:
  limits = settings["limits"]
  return run_bounded(
    command,
    timeout_seconds=limits["command_timeout_seconds"],
    cleanup_timeout_seconds=limits["cleanup_timeout_seconds"],
    max_output_bytes=maximum_output_bytes,
    read_chunk_bytes=limits["read_chunk_bytes"],
  )


def _supports_capture(device: str, settings: Settings) -> bool:
  template = settings["commands"]["device_info"]
  command = [part.replace("{device}", device) for part in template]
  result = _bounded_output(command, settings["limits"]["maximum_device_info_output_bytes"], settings)
  if result is None:
    return False
  parsing = settings["parsing"]
  inspect_caps = False
  for line in result.decode("utf-8", errors="replace").splitlines():
    stripped = line.lstrip()
    if stripped.startswith(parsing["device_caps_marker"]):
      inspect_caps = True
    elif inspect_caps and stripped.startswith(parsing["capture_capability_prefix"]):
      return True
  return False


def list_capture_devices(settings: Settings) -> list[str]:
  listing = _bounded_output(
    settings["commands"]["list_devices"],
    settings["limits"]["maximum_list_output_bytes"],
    settings,
  )
  if listing is None:
    return []
  device_pattern = re.compile(settings["parsing"]["video_node_pattern"])
  devices: list[str] = []
  name = ""
  emitted = False
  for line in listing.decode("utf-8", errors="replace").splitlines():
    if not line:
      continue
    if not line[0].isspace():
      name = line
      emitted = False
      continue
    device = line.strip()
    if name and not emitted and device_pattern.fullmatch(device) and _supports_capture(device, settings):
      devices.append(f"{device}{settings['output']['separator']}{name}")
      emitted = True
  return devices


def list_devices_main() -> int:
  settings = _settings()
  devices = list_capture_devices(settings)
  if devices:
    sys.stdout.write(settings["output"]["trailing_newline"].join(devices))
    sys.stdout.write(settings["output"]["trailing_newline"])
  return settings["statuses"]["list_success"]


def main() -> int:
  settings = _settings()
  return settings["statuses"]["detected"] if list_capture_devices(settings) else settings["statuses"]["absent"]
