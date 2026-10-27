"""Set the ASUS ProArt P14 keyboard top row to media keys by default."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/asus/proart-p14-fkeys.yml").read_text(encoding="utf-8"),
  )
  if subprocess.run(config["hardware_check"], check=False).returncode != 0:
    return int(config["statuses"]["complete"])

  target = Path(config["target"])
  if target.is_file():
    return int(config["statuses"]["complete"])
  target.parent.mkdir(parents=True, exist_ok=True)
  with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
    temporary.write(config["content"])
    temporary_path = Path(temporary.name)
  try:
    temporary_path.chmod(int(config["mode"], 8))
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
