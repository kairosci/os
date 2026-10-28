from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import yaml


class Settings(TypedDict):
  command: list[str]


def _settings() -> Settings:
  root = Path(os.environ["ARCH_PATH"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-vm.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise TypeError("hardware virtualization configuration must be a mapping")
  command = raw.get("command")
  if not isinstance(command, list) or not all(isinstance(argument, str) for argument in command):
    raise TypeError("hardware virtualization command must be a list of strings")
  return {"command": command}


def main() -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load hardware virtualization configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    result = subprocess.run(settings["command"], check=False)
  except OSError as error:
    print(f"Could not run hardware virtualization detection: {error}", file=sys.stderr)
    return 1
  return result.returncode
