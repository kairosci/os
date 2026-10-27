from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

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

  sys.path.insert(0, str(root / "src/python"))
  from migrations.chromium_flags import add_extension

  extension_path = str(root / config["paths"]["extension"])
  settings = config["values"]
  config_dir = Path.home() / config["paths"]["config_directory"]
  for browser in settings["browsers"]:
    flags_file = config_dir / f"{browser}{settings['flags_suffix']}"
    add_extension(
      flags_file,
      settings["extension_marker"],
      settings["load_extension_option"],
      extension_path,
    )

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
