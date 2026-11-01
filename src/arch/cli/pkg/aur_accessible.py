from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  command: list[str]
  timeout: int
  available: int
  unavailable: int


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError("AUR connectivity settings must be mappings")
  return cast(dict[str, object], value)


def _status(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise TypeError("AUR connectivity status values must be non-negative integers")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/pkg-aur-accessible.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  commands = _mapping(document.get("commands"))
  limits = _mapping(document.get("limits"))
  statuses = _mapping(document.get("statuses"))
  command = commands.get("check")
  timeout = limits.get("timeout_seconds")
  if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
    raise TypeError("AUR connectivity command must be a non-empty string list")
  if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
    raise TypeError("AUR connectivity timeout must be a positive integer")
  return {
    "command": cast(list[str], command),
    "timeout": timeout,
    "available": _status(statuses.get("available")),
    "unavailable": _status(statuses.get("unavailable")),
  }


def main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load AUR connectivity configuration: {error}", file=sys.stderr)
    return 2

  try:
    result = subprocess.run(
      settings["command"],
      check=False,
      stdin=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      timeout=settings["timeout"],
    )
  except (OSError, subprocess.SubprocessError):
    return settings["unavailable"]
  return settings["available"] if result.returncode == settings["available"] else settings["unavailable"]
