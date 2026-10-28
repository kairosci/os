from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import yaml


def _command() -> list[str]:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/restart-hyprland.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise ValueError("restart configuration must be a mapping")
  command = raw.get("command")
  if not isinstance(command, list) or not all(isinstance(argument, str) for argument in command):
    raise ValueError("restart configuration command must be a list of strings")
  return [argument for argument in command if isinstance(argument, str)]


def main() -> int:
  try:
    command = _command()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load Hyprland restart configuration: {error}", file=sys.stderr)
    return 1
  try:
    result = subprocess.run(command, check=False, stdout=subprocess.DEVNULL)
  except OSError as error:
    print(f"Could not restart Hyprland: {error}", file=sys.stderr)
    return 1
  return result.returncode
