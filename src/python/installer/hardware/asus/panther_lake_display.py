"""Install Panther Lake display workarounds on supported ASUS laptops."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/asus/panther-lake-display.yml").read_text(encoding="utf-8"),
  )
  for setup in config["setups"]:
    if not any(subprocess.run(check, check=False).returncode == 0 for check in setup["checks"]):
      continue
    with tempfile.TemporaryDirectory() as temporary_directory:
      source = Path(temporary_directory) / Path(setup["target"]).name
      source.write_text(setup["content"], encoding="utf-8")
      subprocess.run(
        [*config["install_file"], str(source), setup["target"]],
        check=True,
      )
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
