from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["vulkan_setup"]
  packages: list[str] = []
  try:
    result = subprocess.run(settings["pci_command"], check=False, capture_output=True, text=True)
  except OSError:
    result = None
  pci_output = result.stdout if result is not None and result.returncode == 0 else ""
  for rule in settings["driver_rules"]:
    if re.search(rule["pattern"], pci_output, flags=re.IGNORECASE):
      packages.append(rule["package"])

  if subprocess.run(settings["platform_check"], check=False).returncode == 0:
    packages.append(settings["platform_package"])
  if packages:
    return subprocess.run([*settings["package_command"], *packages], check=False).returncode
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
