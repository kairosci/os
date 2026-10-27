from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config(root: Path) -> dict[str, Any]:
  value = yaml.safe_load(
    (root / "data/migrations/1791265613.yml").read_text(encoding="utf-8")
  )
  if not isinstance(value, dict):
    raise ValueError
  return value


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  relative_setup = Path(config["paths"]["firmware_setup"])
  if relative_setup.is_absolute() or ".." in relative_setup.parts:
    return int(config["statuses"]["failure"])
  if subprocess.run(config["commands"]["hardware_check"], check=False).returncode:
    return int(config["statuses"]["success"])

  setup = root / relative_setup
  subprocess.run([*config["commands"]["python"], str(setup)], check=True)
  subprocess.run(config["commands"]["reboot_required"], check=True)
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
