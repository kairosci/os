from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def load_config(root: Path) -> dict:
  config_path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError()
  return config


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  subprocess.run([*config["commands"]["i18n"], config["messages"]["reason"]], check=False)

  home = Path.home()
  link = home / config["paths"]["theme_link"]
  if not link.is_symlink():
    return int(config["statuses"]["success"])

  target = os.readlink(link)
  legacy_targets = {
    str(home / config["paths"]["legacy_absolute_target"]),
    config["paths"]["legacy_relative_target"],
    config["paths"]["legacy_home_target"],
  }
  if target in legacy_targets:
    link.unlink()
    link.symlink_to(config["paths"]["current_relative_target"])

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
