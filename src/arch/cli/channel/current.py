from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import TypedDict

import yaml


class Commands(TypedDict):
  package_query: list[str]
  version_channel: str


class ChannelConfig(TypedDict):
  commands: Commands
  packaged_root_environment: str
  packaged_root_default: str
  development: str
  edge: str
  stable: str
  release_candidate: str
  unknown: str
  development_packages: list[str]
  stable_packages: list[str]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid channel configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid channel configuration: {label} must be a string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid channel configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _settings() -> ChannelConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/channel.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  commands = _mapping(settings.get("commands"), "commands")
  return {
    "commands": {
      "package_query": _text_list(commands.get("package_query"), "commands.package_query"),
      "version_channel": _text(commands.get("version_channel"), "commands.version_channel"),
    },
    "packaged_root_environment": _text(
      settings.get("packaged_root_environment"), "packaged_root_environment"
    ),
    "packaged_root_default": _text(settings.get("packaged_root_default"), "packaged_root_default"),
    "development": _text(settings.get("development"), "development"),
    "edge": _text(settings.get("edge"), "edge"),
    "stable": _text(settings.get("stable"), "stable"),
    "release_candidate": _text(settings.get("release_candidate"), "release_candidate"),
    "unknown": _text(settings.get("unknown"), "unknown"),
    "development_packages": _text_list(settings.get("development_packages"), "development_packages"),
    "stable_packages": _text_list(settings.get("stable_packages"), "stable_packages"),
  }


def _output(command: list[str]) -> tuple[int, str]:
  result = subprocess.run(command, check=False, capture_output=True, text=True)
  return result.returncode, result.stdout.strip()


def channel_current_main() -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load channel configuration: {error}", file=sys.stderr)
    return 2

  root = Path(os.environ["AP"])
  packaged_root = os.environ.get(
    settings["packaged_root_environment"],
    settings["packaged_root_default"],
  )
  if str(root).rstrip("/") != str(packaged_root).rstrip("/"):
    print(settings["development"])
    return 0

  try:
    status, _ = _output([*settings["commands"]["package_query"], *settings["development_packages"]])
    if status == 0:
      print(settings["edge"])
      return 0

    status, _ = _output([*settings["commands"]["package_query"], *settings["stable_packages"]])
    if status == 0:
      status, channel = _output([settings["commands"]["version_channel"]])
      if status == 0:
        channel = channel.split()[0] if channel else settings["unknown"]
        if channel in (settings["stable"], settings["release_candidate"]):
          print(channel)
        else:
          print(settings["unknown"])
      else:
        print(settings["unknown"])
      return 0
    print(settings["unknown"])
    return 0
  except OSError as error:
    print(f"Could not determine the installed Arch channel: {error}", file=sys.stderr)
    return 2
