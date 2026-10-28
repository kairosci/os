from __future__ import annotations

import os
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  for directory in config["work_directories"]["directories"]:
    (Path.home() / directory).mkdir(parents=True, exist_ok=True)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
