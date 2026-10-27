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
    raise ValueError
  return config


def main() -> int:
  config = load_config()
  message = subprocess.run(
    [*config["commands"]["i18n"], config["messages"]["reason"]],
    check=True,
    capture_output=True,
    text=True,
  )
  print(message.stdout.rstrip("\n"))
  result = subprocess.run(
    [*config["commands"]["package_add"], config["package"]],
    check=False,
  )
  return result.returncode


if __name__ == "__main__":
  raise SystemExit(main())
