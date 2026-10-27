"""Install the Framework 16 keyboard's unprivileged QMK udev rule."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/framework16-qmk-hid.yml").read_text(encoding="utf-8"),
  )
  if subprocess.run(config["hardware_check"], check=False).returncode != 0:
    return int(config["statuses"]["complete"])

  target = Path(config["target"])
  if target.is_symlink():
    return int(config["statuses"]["complete"] if target.is_file() else config["statuses"]["failed"])
  if target.is_file():
    return int(config["statuses"]["complete"])
  if target.exists():
    return int(config["statuses"]["failed"])

  result = subprocess.run(
    [*config["install_file"], str(root / config["source"]), config["target"]],
    check=False,
  )
  return result.returncode


if __name__ == "__main__":
  raise SystemExit(main())
