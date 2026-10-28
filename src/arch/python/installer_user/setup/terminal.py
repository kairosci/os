from __future__ import annotations

import os
import shutil
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["terminal"]
  applications = Path.home() / settings["applications_directory"]
  applications.mkdir(parents=True, exist_ok=True)

  target = applications / settings["target"]
  shutil.copyfile(root / settings["source"], target)
  target.chmod(int(settings["mode"], 8))

  for entry in applications.glob(settings["obsolete_pattern"]):
    if entry != target:
      entry.unlink()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
