from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("Invalid migration configuration")
  return value


def main() -> int:
  config = load_config()
  root = Path(os.environ["ARCH_PATH"])
  result = subprocess.run(
    [*config["commands"]["python"], str(root / config["script"]), *config["arguments"]],
    check=False,
  )
  return int(result.returncode)


if __name__ == "__main__":
  raise SystemExit(main())
