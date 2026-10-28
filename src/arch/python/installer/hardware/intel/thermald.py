from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["intel_power_setup"]
  setup = settings["thermald"]
  if subprocess.run(setup["checks"][0], check=False).returncode:
    return 0

  try:
    cpu_info = Path(settings["cpu_info_file"]).read_text(encoding="utf-8", errors="replace")
  except OSError:
    cpu_info = ""
  model = re.search(settings["cpu_model_pattern"], cpu_info, flags=re.MULTILINE)
  cpu_model = int(model.group(1)) if model else int(setup["missing_cpu_model"])
  if cpu_model < int(setup["minimum_cpu_model"]):
    return 0
  if subprocess.run(setup["battery_check"], check=False).returncode:
    return 0

  result = subprocess.run(setup["package_command"], check=False)
  if result.returncode:
    return result.returncode
  return subprocess.run(setup["enable_command"], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
