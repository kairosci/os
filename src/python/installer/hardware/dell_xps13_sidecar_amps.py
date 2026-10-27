"""Enable the sidecar amplifier workaround on the Dell XPS 13 DX13260."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/dell-xps13-sidecar-amps.yml").read_text(encoding="utf-8"),
  )
  if subprocess.run(config["hardware_check"], check=False).returncode != 0:
    return int(config["statuses"]["complete"])

  subprocess.run(config["install_package"], check=True)
  subprocess.run(config["apply_workaround"], check=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
