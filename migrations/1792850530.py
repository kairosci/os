from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  value = yaml.safe_load((root / "data/migrations/1792850530.yml").read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("invalid branding migration configuration")
  return value


def main() -> int:
  config = load_config()
  root = Path(os.environ["ARCH_PATH"])
  message = subprocess.run(
    [*config["commands"]["i18n"], config["message"]],
    check=False,
    capture_output=True,
    text=True,
  ).stdout.rstrip("\n")
  print(message)
  command = [
    *config["commands"]["elevate"],
    f"ARCH_PATH={root}",
    *config["commands"]["python"],
    str(root / config["paths"]["branding_setup"]),
  ]
  return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
