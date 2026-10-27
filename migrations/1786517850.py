from __future__ import annotations

import os
from pathlib import Path
import shutil
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

  cache = Path.home() / config["paths"]["notification_images"]
  if cache.is_symlink() or cache.is_file():
    cache.unlink()
  elif cache.is_dir():
    shutil.rmtree(cache)

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
