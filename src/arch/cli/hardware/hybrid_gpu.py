from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import TypedDict

import yaml


class Commands(TypedDict):
  availability: list[str]
  query: list[str]
  timeout: list[str]


class Paths(TypedDict):
  pci_devices: str
  override_environment: str
  device_glob: str
  class_attribute: str
  attribute_encoding: str


class Patterns(TypedDict):
  display_controller_class_prefix: str


class RuntimeSettings(TypedDict):
  hybrid_mode: str
  minimum_display_controllers: int
  timeout_statuses: list[int]
  query_timeout_seconds: int


class Settings(TypedDict):
  commands: Commands
  paths: Paths
  patterns: Patterns
  settings: RuntimeSettings


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid hybrid GPU configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid hybrid GPU configuration: {label} must be a non-empty string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"invalid hybrid GPU configuration: {label} must be a non-empty list of strings")
  return [item for item in value if isinstance(item, str)]


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 1:
    raise ValueError(f"invalid hybrid GPU configuration: {label} must be a positive integer")
  return value


def _integer_list(value: object, label: str) -> list[int]:
  if not isinstance(value, list) or not all(
    isinstance(item, int) and not isinstance(item, bool) and item > 0 for item in value
  ):
    raise ValueError(f"invalid hybrid GPU configuration: {label} must be a list of positive integers")
  return [item for item in value if isinstance(item, int) and not isinstance(item, bool) and item > 0]


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-hybrid-gpu.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  commands = _mapping(document.get("commands"), "commands")
  paths = _mapping(document.get("paths"), "paths")
  patterns = _mapping(document.get("patterns"), "patterns")
  settings = _mapping(document.get("settings"), "settings")
  return {
    "commands": {
      "availability": _text_list(commands.get("availability"), "commands.availability"),
      "query": _text_list(commands.get("query"), "commands.query"),
      "timeout": _text_list(commands.get("timeout"), "commands.timeout"),
    },
    "paths": {
      "pci_devices": _text(paths.get("pci_devices"), "paths.pci_devices"),
      "override_environment": _text(paths.get("override_environment"), "paths.override_environment"),
      "device_glob": _text(paths.get("device_glob"), "paths.device_glob"),
      "class_attribute": _text(paths.get("class_attribute"), "paths.class_attribute"),
      "attribute_encoding": _text(paths.get("attribute_encoding"), "paths.attribute_encoding"),
    },
    "patterns": {
      "display_controller_class_prefix": _text(
        patterns.get("display_controller_class_prefix"),
        "patterns.display_controller_class_prefix",
      ),
    },
    "settings": {
      "hybrid_mode": _text(settings.get("hybrid_mode"), "settings.hybrid_mode"),
      "minimum_display_controllers": _integer(
        settings.get("minimum_display_controllers"),
        "settings.minimum_display_controllers",
      ),
      "timeout_statuses": _integer_list(settings.get("timeout_statuses"), "settings.timeout_statuses"),
      "query_timeout_seconds": _integer(
        settings.get("query_timeout_seconds"), "settings.query_timeout_seconds"
      ),
    },
  }


def _multiple_display_controllers(settings: Settings) -> bool:
  paths = settings["paths"]
  directory = Path(os.environ.get(paths["override_environment"], paths["pci_devices"]))
  prefix = settings["patterns"]["display_controller_class_prefix"]
  count = 0
  for device in directory.glob(paths["device_glob"]):
    try:
      device_class = (device / paths["class_attribute"]).read_text(
        encoding=paths["attribute_encoding"]
      ).strip()
    except (OSError, UnicodeError):
      continue
    if device_class.startswith(prefix):
      count += 1
  return count >= int(settings["settings"]["minimum_display_controllers"])


def main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(str(error), file=sys.stderr)
    return os.EX_CONFIG

  availability = subprocess.run(settings["commands"]["availability"], check=False)
  if availability.returncode != 0:
    return 0 if _multiple_display_controllers(settings) else 1

  try:
    result = subprocess.run(
      [*settings["commands"]["timeout"], *settings["commands"]["query"]],
      check=False,
      capture_output=True,
      text=True,
      timeout=int(settings["settings"]["query_timeout_seconds"]),
    )
  except subprocess.TimeoutExpired:
    return 0 if _multiple_display_controllers(settings) else 1
  except OSError:
    return 1

  if result.returncode in settings["settings"]["timeout_statuses"]:
    return 0 if _multiple_display_controllers(settings) else 1
  return 0 if settings["settings"]["hybrid_mode"] in result.stdout.split() else 1
