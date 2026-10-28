"""Enable Flexible Return and Event Delivery on Intel Panther Lake."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["intel_panther_lake_fred"]
  if subprocess.run(settings["hardware_check"], check=False).returncode != 0:
    return 0

  target = Path(settings["target"])
  content = settings["content"]
  if target.is_file() and re.search(settings["enabled_pattern"], target.read_text(encoding="utf-8")):
    return 0

  with tempfile.TemporaryDirectory() as temporary_directory:
    source = Path(temporary_directory) / target.name
    source.write_text(content, encoding="utf-8")
    return subprocess.run(
      [*settings["install_command"], str(source), str(target)],
      check=False,
    ).returncode


if __name__ == "__main__":
  raise SystemExit(main())
