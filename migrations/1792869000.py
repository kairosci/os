from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config(root: Path) -> dict[str, Any]:
  path = root / "data/migrations" / f"{Path(__file__).stem}.yml"
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("invalid initramfs hooks migration configuration")
  return value


def localized(config: dict[str, Any]) -> str:
  result = subprocess.run(
    [*config["commands"]["i18n"], config["message"]],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  print(localized(config))
  paths = config["paths"]
  config_dir = Path(os.environ.get(paths["config_dir_environment"]) or paths["config_dir_default"])

  for item in paths["files"]:
    source = root / item["source"]
    destination = config_dir / item["destination"]
    result = subprocess.run(
      [*config["commands"]["install"], str(source), str(destination)],
      check=False,
    )
    if result.returncode != 0:
      return result.returncode

  result = subprocess.run(config["commands"]["rebuild"], check=False)
  return result.returncode


if __name__ == "__main__":
  raise SystemExit(main())
