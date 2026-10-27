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
  success = int(config["statuses"]["success"])

  for kernel in config["packages"]["kernels"]:
    installed = subprocess.run(
      [*config["commands"]["package_present"], kernel], check=False
    )
    if installed.returncode == success:
      subprocess.run(
        [*config["commands"]["package_add"], f"{kernel}{config['packages']['header_suffix']}"],
        check=True,
      )

  return success


if __name__ == "__main__":
  raise SystemExit(main())
