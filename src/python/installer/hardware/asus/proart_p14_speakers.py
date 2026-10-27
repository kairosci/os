"""Install ASUS ProArt P14 speaker tuning firmware."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware/asus/proart-p14.yml").read_text(encoding="utf-8"))
  if subprocess.run(config["hardware_check"], check=False).returncode != 0:
    return int(config["statuses"]["complete"])
  return subprocess.run(config["speakers"]["install_packages"], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
