from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["bluetooth_setup"]
  result = subprocess.run(settings["enable_command"], check=False)
  if result.returncode:
    return result.returncode

  if os.environ.get(settings["deferred_environment"]) == settings["deferred_value"]:
    subprocess.run(settings["start_command"], check=False)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
