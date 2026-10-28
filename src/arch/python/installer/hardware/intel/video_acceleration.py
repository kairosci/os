"""Install the VA-API driver matching an Intel GPU generation."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["intel_video_acceleration"]
  result = subprocess.run(settings["pci_command"], check=False, capture_output=True, text=True)
  if result.returncode != 0:
    return result.returncode

  gpu_lines = [
    line for line in result.stdout.splitlines()
    if re.search(settings["gpu_line_pattern"], line, re.IGNORECASE)
  ]
  if any(re.search(settings["modern_gpu_pattern"], line, re.IGNORECASE) for line in gpu_lines):
    packages = settings["modern_packages"]
  elif any(re.search(settings["legacy_gpu_pattern"], line, re.IGNORECASE) for line in gpu_lines):
    packages = settings["legacy_packages"]
  else:
    return 0

  return subprocess.run([*settings["package_command"], *packages], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
