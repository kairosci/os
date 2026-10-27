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
    raise ValueError("invalid sudo grant migration configuration")
  return value


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  message = subprocess.run(
    [*config["commands"]["i18n"], config["message"]],
    check=False,
    capture_output=True,
    text=True,
  )
  print(message.stdout.rstrip("\n"))

  helper = root / config["paths"]["helper"]
  complete = subprocess.run(
    [str(helper), *config["arguments"]["complete"]],
    check=False,
  )
  if complete.returncode == int(config["statuses"]["complete"]):
    return int(config["statuses"]["complete"])

  elevated = subprocess.run(
    [*config["commands"]["elevate"], str(helper), *config["arguments"]["migrate"]],
    check=False,
  )
  return elevated.returncode


if __name__ == "__main__":
  raise SystemExit(main())
