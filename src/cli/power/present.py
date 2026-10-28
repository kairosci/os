from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/power-present.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid power presence configuration")
  return config


def read_value(path: Path) -> str | None:
  try:
    return path.read_text(encoding="utf-8").strip()
  except OSError:
    return None


def has_external_power(config: dict[str, Any]) -> bool:
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
  config = settings()
  status = config["statuses"]
  if has_external_power(config):
    return int(status["connected"])
  return int(status["disconnected"])


if __name__ == "__main__":
  raise SystemExit(main())
