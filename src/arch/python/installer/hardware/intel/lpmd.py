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
  setup = settings["lpmd"]
  for command in setup["checks"]:
    if subprocess.run(command, check=False).returncode:
      return 0

  try:
    cpu_info = Path(settings["cpu_info_file"]).read_text(encoding="utf-8", errors="replace")
  except OSError:
    return 0
  model = re.search(settings["cpu_model_pattern"], cpu_info, flags=re.MULTILINE)
  if model is None or int(model.group(1)) not in setup["supported_cpu_models"]:
    return 0

  result = subprocess.run(setup["package_command"], check=False)
  if result.returncode:
    return result.returncode
  return subprocess.run(setup["enable_command"], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
