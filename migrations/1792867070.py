from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  value = yaml.safe_load(
    (root / "data/migrations" / f"{Path(__file__).stem}.yml").read_text(encoding="utf-8"),
  )
  if not isinstance(value, dict):
    raise ValueError("invalid terminal migration configuration")
  command = [*value["commands"]["python"], str(root / value["paths"]["setup"])]
  return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
