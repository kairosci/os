"""Disable broken EHT on affected Intel Wi-Fi 7 adapters."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["intel_wifi7_eht_workaround"]
  statuses = settings["statuses"]
  result = subprocess.run(settings["pci_command"], check=False, capture_output=True, text=True)
  if result.returncode != 0:
    return result.returncode
  if not re.search(settings["device_pattern"], result.stdout, re.IGNORECASE):
    return int(statuses["complete"])

  target = Path(settings["target"])
  if target.is_symlink():
    return int(statuses["failed"])
  content = settings["content"]
  if target.is_file() and target.read_text(encoding="utf-8") == content:
    return int(statuses["complete"])

  target.parent.mkdir(parents=True, exist_ok=True)
  with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
    temporary.write(content)
    temporary_path = Path(temporary.name)
  try:
    temporary_path.chmod(int(settings["mode"], 8))
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)
  return int(statuses["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
