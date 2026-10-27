"""Install Elgato Cam Link 4K virtual camera support."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/elgato-camlink-4k.yml").read_text(encoding="utf-8"),
  )
  if subprocess.run(config["hardware_check"], check=False).returncode != 0:
    return int(config["statuses"]["complete"])

  subprocess.run(config["install_packages"], check=True)
  for item in config["files"]:
    subprocess.run(
      [*config["install_file"], str(root / item["source"]), item["target"]],
      check=True,
    )

  dropin = config["modprobe_dropin"]
  with tempfile.TemporaryDirectory() as temporary_directory:
    source = Path(temporary_directory) / Path(dropin["target"]).name
    source.write_text(dropin["content"], encoding="utf-8")
    subprocess.run(
      [*config["install_file"], str(source), dropin["target"]],
      check=True,
    )
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
