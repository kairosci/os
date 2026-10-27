from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import yaml


def _settings() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/cmd-presence.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid command presence configuration")
  return settings


def _missing(settings: dict) -> bool:
  return any(shutil.which(name) is None for name in sys.argv[1:])


def missing_main() -> int:
  settings = _settings()
  result = "any_missing" if _missing(settings) else "all_present"
  return settings["commands"]["missing"][result]


def present_main() -> int:
  settings = _settings()
  result = "any_missing" if _missing(settings) else "all_present"
  return settings["commands"]["present"][result]
