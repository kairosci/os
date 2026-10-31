from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import yaml


def _predicates() -> list[list[str]]:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-clamshell.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise ValueError("clamshell hardware configuration must be a mapping")
  commands = raw.get("commands")
  if not isinstance(commands, dict):
    raise ValueError("clamshell hardware commands must be a mapping")
  predicates = commands.get("predicates")
  if not isinstance(predicates, list) or not predicates:
    raise ValueError("clamshell hardware predicates must be a non-empty list of argument lists")
  parsed: list[list[str]] = []
  for command in predicates:
    if not isinstance(command, list) or not command:
      raise ValueError("clamshell hardware predicates must be non-empty argument lists")
    arguments: list[str] = []
    for argument in command:
      if not isinstance(argument, str) or not argument:
        raise ValueError("clamshell hardware predicates must contain non-empty strings")
      arguments.append(argument)
    parsed.append(arguments)
  return parsed


def main() -> int:
  try:
    predicates = _predicates()
  except (KeyError, OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load clamshell hardware configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  for command in predicates:
    try:
      result = subprocess.run(command, check=False)
    except OSError as error:
      print(f"Could not run clamshell hardware predicate: {error}", file=sys.stderr)
      return 1
    if result.returncode != 0:
      return result.returncode
  return 0
