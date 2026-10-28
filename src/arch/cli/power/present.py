from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TypedDict

import yaml


class Paths(TypedDict):
  power_supply: str
  override_environment: str
  type_file: str
  online_file: str


class Values(TypedDict):
  external_types: list[str]
  online: str


class Statuses(TypedDict):
  connected: int
  disconnected: int


class PowerConfig(TypedDict):
  paths: Paths
  values: Values
  statuses: Statuses


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid power presence configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid power presence configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid power presence configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list):
    raise TypeError(f"invalid power presence configuration: {label} must be a list")
  return [_text(item, f"{label} item") for item in value]


def settings() -> PowerConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/power-present.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  paths = _mapping(config.get("paths"), "paths")
  values = _mapping(config.get("values"), "values")
  statuses = _mapping(config.get("statuses"), "statuses")
  return {
    "paths": {
      "power_supply": _text(paths.get("power_supply"), "paths.power_supply"),
      "override_environment": _text(paths.get("override_environment"), "paths.override_environment"),
      "type_file": _text(paths.get("type_file"), "paths.type_file"),
      "online_file": _text(paths.get("online_file"), "paths.online_file"),
    },
    "values": {
      "external_types": _text_list(values.get("external_types"), "values.external_types"),
      "online": _text(values.get("online"), "values.online"),
    },
    "statuses": {
      "connected": _integer(statuses.get("connected"), "statuses.connected"),
      "disconnected": _integer(statuses.get("disconnected"), "statuses.disconnected"),
    },
  }


def read_value(path: Path) -> str | None:
  try:
    return path.read_text(encoding="utf-8").strip()
  except OSError:
    return None


def has_external_power(config: PowerConfig) -> bool:
  paths = config["paths"]
  values = config["values"]
  root = Path(os.environ.get(paths["override_environment"], paths["power_supply"]))
  try:
    supplies = sorted(root.iterdir())
  except OSError:
    return False

  for supply in supplies:
    supply_type = read_value(supply / paths["type_file"])
    online = read_value(supply / paths["online_file"])
    if supply_type in values["external_types"] and online == values["online"]:
      return True
  return False


def main() -> int:
  try:
    config = settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load power presence configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  status = config["statuses"]
  if has_external_power(config):
    return int(status["connected"])
  return int(status["disconnected"])


if __name__ == "__main__":
  raise SystemExit(main())
