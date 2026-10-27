"""Apply the next-boot GPU memory reservation on NVIDIA N1x systems."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/n1x-gpu-memory.yml").read_text(encoding="utf-8"),
  )
  if subprocess.run(config["commands"]["hardware_match"], check=False).returncode == int(config["statuses"]["matched"]):
    subprocess.run(config["commands"]["apply"], check=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
