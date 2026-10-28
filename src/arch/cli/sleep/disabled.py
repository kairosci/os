"""Check the shared sleep-disable setting."""

from __future__ import annotations

import os
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/system/sleep.yml").read_text(encoding="utf-8"))
  directory = os.environ.get(config["directory_environment"]) or config["directory_default"]
  disabled = (Path(directory) / config["disabled_filename"]).is_file()
  status = "complete" if disabled else "enabled"
  return int(config["statuses"][status])
