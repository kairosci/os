from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["git_identity"]
  for entry in settings["values"]:
    value = os.environ.get(entry["environment"], "")
    if not any(not character.isspace() for character in value):
      continue
    result = subprocess.run(
      [*settings["command"], entry["key"], value],
      check=False,
    )
    if result.returncode != 0:
      return result.returncode
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
