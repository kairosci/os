from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/system-setup.yml").read_text(encoding="utf-8"))
  settings = config["chromium_preferences"]
  destination = Path(settings["destination"])
  destination.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(dir=destination.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(settings["content"])
      output.write("\n")
      output.flush()
      os.fsync(output.fileno())
      os.fchmod(output.fileno(), settings["mode"])
    os.replace(temporary, destination)
  finally:
    temporary.unlink(missing_ok=True)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
