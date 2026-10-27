from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
  value = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError(f"Invalid migration configuration: {path}")
  return value


def main(migration_path: Path) -> int:
  root = Path(os.environ["ARCH_PATH"])
  migration = load_yaml(root / "data/migrations" / f"{migration_path.stem}.yml")
  runner = load_yaml(root / "data/cli/migration-commands.yml")

  translated = subprocess.run(
    [*runner["commands"]["i18n"], migration["messages"]["reason"]],
    check=True,
    capture_output=True,
    text=True,
  )
  print(translated.stdout.rstrip("\n"))

  for step in migration["steps"]:
    command = subprocess.run(step["command"], check=False)
    if command.returncode and not step.get("ignore_failure", False):
      return command.returncode or int(runner["statuses"]["failure"])
  return int(runner["statuses"]["success"])
