from __future__ import annotations

import os
from pathlib import Path
import subprocess
import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/webcam.yml").read_text(encoding="utf-8"))
  result = subprocess.run(config["commands"]["list_devices"], check=False, capture_output=True, text=True)
  output = result.stdout.rstrip(config["output"]["trailing_newline"])
  return 0 if output else 1
