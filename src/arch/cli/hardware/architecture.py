from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Literal, TypedDict

import yaml


class Commands(TypedDict):
  platform_detector: list[str]


class Platforms(TypedDict):
  x86: str
  aarch64_prefix: str


class ArchitectureConfig(TypedDict):
  commands: Commands
  platforms: Platforms


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid architecture configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid architecture configuration: {label} must be a string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid architecture configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _settings() -> ArchitectureConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/architecture.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  commands = _mapping(settings.get("commands"), "commands")
  platforms = _mapping(settings.get("platforms"), "platforms")
  return {
    "commands": {
      "platform_detector": _text_list(commands.get("platform_detector"), "commands.platform_detector"),
    },
    "platforms": {
      "x86": _text(platforms.get("x86"), "platforms.x86"),
      "aarch64_prefix": _text(platforms.get("aarch64_prefix"), "platforms.aarch64_prefix"),
    },
  }


def _platform(settings: ArchitectureConfig) -> str | None:
  root = Path(os.environ["AP"])
  command = settings["commands"]["platform_detector"]
  detector = [str(root / command[0]), *command[1:]]
  try:
    result = subprocess.run(detector, check=False, capture_output=True, text=True)
  except OSError:
    return None
  if result.returncode != 0:
    return None
  return result.stdout.strip()


def _main(architecture: Literal["x86", "aarch64"]) -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load architecture configuration: {error}", file=sys.stderr)
    return 2
  platform = _platform(settings)
  if architecture == "x86":
    return 0 if platform == settings["platforms"]["x86"] else 1
  return 0 if platform is not None and platform.startswith(settings["platforms"]["aarch64_prefix"]) else 1


def x86_main() -> int:
  return _main("x86")


def aarch64_main() -> int:
  return _main("aarch64")
