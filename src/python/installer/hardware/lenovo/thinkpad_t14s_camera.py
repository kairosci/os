"""Install camera support and its DMA heap ACL on Snapdragon ThinkPad T14s systems."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import yaml


def load_config() -> tuple[Path, dict]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/lenovo/thinkpad-t14s-camera.yml").read_text(encoding="utf-8"),
  )
  return root, config


def matches(config: dict) -> bool:
  if subprocess.run(config["commands"]["soc_match"], check=False).returncode != int(config["statuses"]["matched"]):
    return False
  if subprocess.run(
    [*config["commands"]["model_match"], config["hardware"]["model_pattern"]],
    check=False,
  ).returncode != int(config["statuses"]["matched"]):
    return False
  return True


def main() -> int:
  root, config = load_config()
  migration = sys.argv[1:] == ["--migration"]
  if sys.argv[1:] and not migration:
    return int(config["statuses"]["failed"])
  if not matches(config):
    return int(config["statuses"]["complete"])

  subprocess.run(config["commands"]["install_package"], check=True)
  source = root / config["paths"]["rule_source"]
  subprocess.run(
    [*config["commands"]["install_rule"], str(source), config["paths"]["rule_target"]],
    check=True,
  )
  if migration:
    for action in ("reload_udev", "trigger_udev", "settle_udev"):
      subprocess.run(config["commands"][action], check=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
