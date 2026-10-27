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


def run(config: dict[str, Any], command: str, *arguments: str) -> None:
  subprocess.run([*config["commands"][command], *arguments], check=True)


def main(migration_path: Path) -> int:
  root = Path(os.environ["ARCH_PATH"])
  name = migration_path.stem
  migration_config = load_yaml(root / "data/migrations" / f"{name}.yml")
  command_config = load_yaml(root / "data/cli/migration-packages.yml")

  reason = migration_config["messages"]["reason"]
  translated = subprocess.run(
    [*command_config["commands"]["i18n"], reason],
    check=True,
    capture_output=True,
    text=True,
  )
  print(translated.stdout.rstrip("\n"))

  packages = migration_config["packages"]
  if packages["add"]:
    run(command_config, "package_add", *packages["add"])
  if packages["drop"]:
    run(command_config, "package_drop", *packages["drop"])
  return 0
