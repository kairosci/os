"""Disable unreliable Broadcom WPA offload on affected Intel Macs."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/apple/brcmfmac-supplicant.yml").read_text(encoding="utf-8"),
  )
  statuses = config["statuses"]
  if subprocess.run(config["apple_silicon_check"], check=False).returncode == int(statuses["complete"]):
    return int(statuses["complete"])

  vendor_file = Path(
    os.environ.get(config["apple_vendor_environment"]) or config["apple_vendor_default"],
  )
  try:
    vendor = vendor_file.read_text(encoding="utf-8")
  except OSError:
    vendor = ""
  pci = subprocess.run(config["pci_command"], check=False, capture_output=True, text=True)
  if pci.returncode != 0:
    return pci.returncode

  t2_match = re.search(config["t2_pattern"], pci.stdout, re.IGNORECASE) is not None
  wifi_match = (
    re.search(config["apple_vendor_pattern"], vendor, re.IGNORECASE) is not None
    and re.search(config["wifi_pattern"], pci.stdout, re.IGNORECASE) is not None
  )
  if not (t2_match or wifi_match):
    return int(statuses["complete"])

  system_root = Path(os.environ.get(config["system_root_environment"]) or "/")
  target = system_root / config["target"]
  if target.is_symlink():
    return int(statuses["failed"])
  target.parent.mkdir(parents=True, exist_ok=True)
  with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
    temporary.write(config["content"])
    temporary_path = Path(temporary.name)
  try:
    temporary_path.chmod(int(config["mode"], 8))
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)
  return int(statuses["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
