from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["qualcomm_camera"]
  if subprocess.run(settings["check_command"], check=False).returncode != 0:
    return 0
  command = [*settings["package_command"], settings["package"]]
  return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
