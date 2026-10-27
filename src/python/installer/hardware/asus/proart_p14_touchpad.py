"""Install the libinput pressure-pad quirk for ASUS ProArt P14."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware/asus/proart-p14.yml").read_text(encoding="utf-8"))
  if subprocess.run(config["hardware_check"], check=False).returncode != 0:
    return int(config["statuses"]["complete"])

  settings = config["touchpad"]
  target = Path(settings["target"])
  if target.is_symlink():
    return int(config["statuses"]["failed"])
  existing = target.read_text(encoding="utf-8") if target.is_file() else ""
  if settings["section_header"] in existing.splitlines():
    return int(config["statuses"]["complete"])

  target.parent.mkdir(parents=True, exist_ok=True)
  mode = stat.S_IMODE(target.stat().st_mode) if target.is_file() else int(settings["mode"], 8)
  with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
    temporary.write(existing)
    temporary.write(settings["content"])
    temporary_path = Path(temporary.name)
  try:
    temporary_path.chmod(mode)
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
