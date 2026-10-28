from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def _installed(command: list[str], package: str) -> bool:
  try:
    return subprocess.run([*command, package], check=False).returncode == 0
  except OSError:
    return False


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["nvidia_apps_setup"]

  if _installed(settings["package_check_command"], settings["workbench_package"]):
    result = subprocess.run(settings["workbench_command"], check=False)
    if result.returncode:
      return result.returncode

  if _installed(settings["package_check_command"], settings["dashboard_package"]):
    result = subprocess.run(settings["enable_command"], check=False)
    if result.returncode:
      return result.returncode
    if os.environ.get(settings["deferred_environment"]) == settings["deferred_value"]:
      subprocess.run(settings["start_command"], check=False)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
