from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["package_gates"]
  failure_status = 0
  for rule in settings["rules"]:
    matched = True
    for check in rule["checks"]:
      if subprocess.run(check, check=False).returncode != 0:
        matched = False
        break
    if not matched:
      continue
    command = [*settings["package_command"], *rule["packages"]]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
      failure_status = result.returncode
  return failure_status


if __name__ == "__main__":
  raise SystemExit(main())
