from __future__ import annotations

import os
from pathlib import Path
import re
import sys
from typing import TypedDict

import yaml


class Paths(TypedDict):
  acpi_lid_default: str
  acpi_lid_environment: str
  acpi_state_glob: str
  input_class_default: str
  input_class_environment: str
  input_switch_glob: str
  chassis_type_default: str
  chassis_type_environment: str


class Identifiers(TypedDict):
  switch_capability_pattern: str
  lid_switch_mask: int
  laptop_chassis_types: list[str]


class Settings(TypedDict):
  paths: Paths
  identifiers: Identifiers


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid laptop hardware configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid laptop hardware configuration: {label} must be a non-empty string")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-laptop.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  raw_paths = _mapping(document.get("paths"), "paths")
  raw_identifiers = _mapping(document.get("identifiers"), "identifiers")
  mask = raw_identifiers.get("lid_switch_mask")
  chassis_types = raw_identifiers.get("laptop_chassis_types")
  if not isinstance(mask, int) or isinstance(mask, bool) or mask < 0:
    raise ValueError("invalid laptop hardware configuration: identifiers.lid_switch_mask must be a non-negative integer")
  if not isinstance(chassis_types, list) or not all(isinstance(value, str) for value in chassis_types):
    raise ValueError("invalid laptop hardware configuration: identifiers.laptop_chassis_types must be a list of strings")
  return {
    "paths": {
      "acpi_lid_default": _text(raw_paths.get("acpi_lid_default"), "paths.acpi_lid_default"),
      "acpi_lid_environment": _text(raw_paths.get("acpi_lid_environment"), "paths.acpi_lid_environment"),
      "acpi_state_glob": _text(raw_paths.get("acpi_state_glob"), "paths.acpi_state_glob"),
      "input_class_default": _text(raw_paths.get("input_class_default"), "paths.input_class_default"),
      "input_class_environment": _text(raw_paths.get("input_class_environment"), "paths.input_class_environment"),
      "input_switch_glob": _text(raw_paths.get("input_switch_glob"), "paths.input_switch_glob"),
      "chassis_type_default": _text(raw_paths.get("chassis_type_default"), "paths.chassis_type_default"),
      "chassis_type_environment": _text(raw_paths.get("chassis_type_environment"), "paths.chassis_type_environment"),
    },
    "identifiers": {
      "switch_capability_pattern": _text(raw_identifiers.get("switch_capability_pattern"), "identifiers.switch_capability_pattern"),
      "lid_switch_mask": mask,
      "laptop_chassis_types": chassis_types,
    },
  }


def _has_acpi_lid(settings: Settings) -> bool:
  paths = settings["paths"]
  root = Path(os.environ.get(paths["acpi_lid_environment"], paths["acpi_lid_default"]))
  try:
    return any(state.exists() for state in root.glob(paths["acpi_state_glob"]))
  except OSError:
    return False


def _has_lid_switch(settings: Settings) -> bool:
  paths = settings["paths"]
  identifiers = settings["identifiers"]
  root = Path(os.environ.get(paths["input_class_environment"], paths["input_class_default"]))
  pattern = re.compile(identifiers["switch_capability_pattern"])
  try:
    for switch_file in root.glob(paths["input_switch_glob"]):
      try:
        with switch_file.open(encoding="ascii") as stream:
          first_line = stream.readline()
      except (OSError, UnicodeError):
        continue
      words = first_line.split()
      if words and pattern.fullmatch(words[-1]):
        if int(words[-1], 16) & identifiers["lid_switch_mask"]:
          return True
  except OSError:
    return False
  return False


def _has_laptop_chassis(settings: Settings) -> bool:
  paths = settings["paths"]
  chassis_path = Path(os.environ.get(paths["chassis_type_environment"], paths["chassis_type_default"]))
  try:
    with chassis_path.open(encoding="ascii") as stream:
      chassis_type = stream.readline().rstrip("\n")
  except (OSError, UnicodeError):
    return False
  return chassis_type in settings["identifiers"]["laptop_chassis_types"]


def laptop_main() -> int:
  try:
    settings = _settings()
    return 0 if _has_acpi_lid(settings) or _has_lid_switch(settings) or _has_laptop_chassis(settings) else 1
  except (KeyError, OSError, UnicodeError, TypeError, ValueError, re.error, yaml.YAMLError) as error:
    print(f"{error}", file=sys.stderr)
    return os.EX_CONFIG
