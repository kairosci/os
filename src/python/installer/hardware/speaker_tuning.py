from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["speaker_tuning"]
  matched = subprocess.run(settings["match_command"], check=False, stdout=subprocess.DEVNULL)
  if matched.returncode != 0:
    return 0
  return subprocess.run([*settings["package_command"], *settings["packages"]], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
