"""Install Intel IPU7 MIPI camera support when its ACPI device is present."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/intel/ipu7-camera.yml").read_text(encoding="utf-8"),
  )
  directory = Path(config["paths"]["acpi_devices"])
  hid_paths = directory.glob(config["paths"]["hid_pattern"])
  if any(
    config["hardware"]["acpi_hid"] in path.read_text(
      encoding=config["encoding"], errors="replace",
    )
    for path in hid_paths
    if path.is_file()
  ):
    subprocess.run(config["commands"]["install"], check=True)
    return int(config["statuses"]["matched"])
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
