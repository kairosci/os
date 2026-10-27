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

  installed = subprocess.run(
    [*config["commands"]["present"], *config["packages"]["retired"]],
    check=False,
  )
  if installed.returncode != int(config["statuses"]["present"]):
    return int(config["statuses"]["success"])

  result = subprocess.run(
    [
      *config["commands"]["elevate"],
      *config["commands"]["package_manager"],
      *config["arguments"]["replace"],
    ],
    check=False,
  )
  return result.returncode


if __name__ == "__main__":
  raise SystemExit(main())
