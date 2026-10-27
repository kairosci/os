from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config: Any = yaml.safe_load((root / "data/cli/hardware-vm.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict) or not isinstance(config.get("command"), list):
    return 1
  try:
    result = subprocess.run(config["command"], check=False)
  except OSError:
    return 1
  return result.returncode
