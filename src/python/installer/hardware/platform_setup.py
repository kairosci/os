"""Run the platform packages' final system setup operations."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/platform-setup.yml").read_text(encoding="utf-8"),
  )
  deferred = os.environ.get(config["deferred_environment"]) == config["deferred_value"]
  argument_key = "deferred_arguments" if deferred else "arguments"
  for operation in config["operations"]:
    result = subprocess.run(
      [*config["dispatch_command"], operation["name"], *operation[argument_key]],
      check=False,
    )
    if result.returncode != int(config["statuses"]["complete"]):
      return result.returncode
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
