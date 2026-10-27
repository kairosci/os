from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("Invalid migration configuration")
  return config


def main() -> int:
  config = load_config()
  subprocess.run(
    [*config["commands"]["i18n"], config["messages"]["reason"]], check=True
  )

  home = Path.home()
  marker = home / config["paths"]["preinstalls_removed"]
  if not marker.exists():
    subprocess.run(
      [*config["commands"]["install"], *config["install"]], check=True
    )

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
