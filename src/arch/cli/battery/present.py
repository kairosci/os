from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/battery-present.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid battery presence configuration")
  return config


def read_value(path: Path) -> str | None:
  try:
    return path.read_text(encoding="utf-8").strip()
  except OSError:
    return None


def has_battery(config: dict[str, Any]) -> bool:
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
  config = settings()
  status = config["statuses"]
  if has_battery(config):
    return int(status["present"])
  return int(status["absent"])


if __name__ == "__main__":
  raise SystemExit(main())
