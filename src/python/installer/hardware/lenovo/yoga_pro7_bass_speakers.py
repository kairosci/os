"""Install the audio pin quirk for the Lenovo Yoga Pro 7 14IAH10."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/lenovo/yoga-pro7-bass-speakers.yml").read_text(encoding="utf-8"),
  )
  if subprocess.run(config["hardware_check"], check=False).returncode != 0:
    return int(config["statuses"]["complete"])

  with tempfile.TemporaryDirectory() as temporary_directory:
    source = Path(temporary_directory) / Path(config["target"]).name
    source.write_text(config["content"], encoding="utf-8")
    subprocess.run([*config["install_file"], str(source), config["target"]], check=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
