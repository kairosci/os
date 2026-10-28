from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/system-setup.yml").read_text(encoding="utf-8"))
  settings = config["lockscreen"]
  command = [part.format(ap=root) for part in settings["command"]]
  return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
