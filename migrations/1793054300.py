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
    raise ValueError("invalid retired command shim migration configuration")
  return value


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = load_config(root)
  localized = subprocess.run(
    [*config["commands"]["i18n"], config["message"]],
    check=False,
    capture_output=True,
    text=True,
  )
  print(localized.stdout.rstrip("\n"))

  available = subprocess.run(config["commands"]["runtime_check"], check=False)
  if available.returncode == 0:
    subprocess.run(config["commands"]["system_reshim"], check=False)
    result = subprocess.run(config["commands"]["user_reshim"], check=False)
    return result.returncode

  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
