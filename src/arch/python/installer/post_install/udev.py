from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/post-install.yml").read_text(encoding="utf-8"))
  for command in config["udev"]["commands"]:
    subprocess.run(command, check=False, stderr=subprocess.DEVNULL)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
