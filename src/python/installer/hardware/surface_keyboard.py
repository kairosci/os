"""Add Surface keyboard modules to the initramfs when available."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["surface_keyboard_setup"]
  if any(subprocess.run(check, check=False).returncode != 0 for check in settings["hardware_checks"]):
    return int(settings["statuses"]["complete"])

  result = subprocess.run(settings["loaded_modules_command"], check=False, capture_output=True, text=True)
  if result.returncode != 0:
    return int(settings["statuses"]["complete"])
  pinctrl_module = next(
    (
      fields[0]
      for line in result.stdout.splitlines()[1:]
      if (fields := line.split()) and re.search(settings["pinctrl_module_pattern"], fields[0])
    ),
    None,
  )
  if pinctrl_module is None:
    return int(settings["statuses"]["complete"])

  target = Path(settings["initramfs_directory"]) / settings["config_filename"]
  target.parent.mkdir(parents=True, exist_ok=True)
  content = f"MODULES=({pinctrl_module} {' '.join(settings['modules'])})\n"
  with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
    temporary.write(content)
    temporary_path = Path(temporary.name)
  try:
    temporary_path.chmod(int(settings["mode"], 8))
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)
  return int(settings["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
