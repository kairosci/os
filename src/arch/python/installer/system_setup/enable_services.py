from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/system-setup.yml").read_text(encoding="utf-8"))
  settings = config["service_commands"]
  for command in settings["commands"]:
    result = subprocess.run(command, check=False)
    if result.returncode:
      return result.returncode
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
