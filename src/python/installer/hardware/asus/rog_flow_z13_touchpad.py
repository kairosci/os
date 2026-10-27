"""Mark the ASUS ROG Flow Z13 touchpad as an internal udev device."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/asus/rog-flow-z13-touchpad.yml").read_text(encoding="utf-8"),
  )
  if any(subprocess.run(check, check=False).returncode != 0 for check in config["hardware_checks"]):
    return int(config["statuses"]["complete"])

  with tempfile.TemporaryDirectory() as temporary_directory:
    source = Path(temporary_directory) / Path(config["target"]).name
    source.write_text(config["content"], encoding="utf-8")
    subprocess.run([*config["install_file"], str(source), config["target"]], check=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
