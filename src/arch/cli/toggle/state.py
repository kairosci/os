from __future__ import annotations

import os
from pathlib import Path
import sys

import yaml


def _state_path(name: str) -> Path:
  parts = name.split("/")
  if not name or any(part in {"", ".", ".."} for part in parts):
    raise ValueError("toggle name must be a relative path without traversal components")
  settings_path = Path(os.environ["AP"]) / "data/cli/toggle-state.yml"
  settings = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid toggle state configuration")
  directory = settings.get("home_relative_state_directory")
  if not isinstance(directory, str) or not directory or Path(directory).is_absolute() or ".." in Path(directory).parts:
    raise ValueError("invalid toggle state directory")
  return Path(os.environ["HOME"]) / directory / name


def enabled_main(args: list[str]) -> int:
  if not args:
    return 1
  try:
    return 0 if _state_path(args[0]).is_file() else 1
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not read toggle state", file=sys.stderr)
    return os.EX_CONFIG
