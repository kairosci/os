from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import TypedDict

import yaml


class Paths(TypedDict):
  power_supply: str
  override_environment: str
  present_file: str
  type_file: str
  scope_file: str


class Values(TypedDict):
  present: str
  battery_type: str
  peripheral_scope: str


class Statuses(TypedDict):
  present: int
  absent: int


class BatteryConfig(TypedDict):
  paths: Paths
  values: Values
  statuses: Statuses


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid battery presence configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid battery presence configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid battery presence configuration: {label} must be an integer")
  return value


def settings() -> BatteryConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/battery-present.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  paths = _mapping(config.get("paths"), "paths")
  values = _mapping(config.get("values"), "values")
  statuses = _mapping(config.get("statuses"), "statuses")
  return {
    "paths": {
      "power_supply": _text(paths.get("power_supply"), "paths.power_supply"),
      "override_environment": _text(paths.get("override_environment"), "paths.override_environment"),
      "present_file": _text(paths.get("present_file"), "paths.present_file"),
      "type_file": _text(paths.get("type_file"), "paths.type_file"),
      "scope_file": _text(paths.get("scope_file"), "paths.scope_file"),
    },
    "values": {
      "present": _text(values.get("present"), "values.present"),
      "battery_type": _text(values.get("battery_type"), "values.battery_type"),
      "peripheral_scope": _text(values.get("peripheral_scope"), "values.peripheral_scope"),
    },
    "statuses": {
      "present": _integer(statuses.get("present"), "statuses.present"),
      "absent": _integer(statuses.get("absent"), "statuses.absent"),
    },
  }


def read_value(path: Path) -> str | None:
  try:
    return path.read_text(encoding="utf-8").strip()
  except OSError:
    return None


def has_battery(config: BatteryConfig) -> bool:
  paths = config["paths"]
  values = config["values"]
  root = Path(os.environ.get(paths["override_environment"], paths["power_supply"]))
  try:
    supplies = sorted(root.iterdir())
  except OSError:
    return False

  for supply in supplies:
    if read_value(supply / paths["present_file"]) != values["present"]:
      continue
    if read_value(supply / paths["type_file"]) != values["battery_type"]:
      continue
    if read_value(supply / paths["scope_file"]) == values["peripheral_scope"]:
      continue
    return True
  return False


def main() -> int:
  try:
    config = settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load battery presence configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  status = config["statuses"]
  return status["present"] if has_battery(config) else status["absent"]


if __name__ == "__main__":
  raise SystemExit(main())
