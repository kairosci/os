from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  for command in config["mise_setup"]["commands"]:
    result = subprocess.run(command, check=False)
    if result.returncode:
      return result.returncode
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
