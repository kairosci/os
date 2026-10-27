from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/cmd-missing.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid command presence configuration")

  for name in sys.argv[1:]:
    if shutil.which(name) is None:
      return settings["exit_codes"]["missing"]
  return settings["exit_codes"]["all_present"]
