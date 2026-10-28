from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Literal, TypedDict

import yaml


class PresenceCommands(TypedDict):
  missing: dict[str, int]
  present: dict[str, int]


class PresenceConfig(TypedDict):
  commands: PresenceCommands


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid command presence configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid command presence configuration: {label} must be an integer")
  return value


def _settings() -> PresenceConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/cmd-presence.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  commands = _mapping(settings.get("commands"), "commands")
  missing = _mapping(commands.get("missing"), "commands.missing")
  present = _mapping(commands.get("present"), "commands.present")
  return {
    "commands": {
      "missing": {
        "any_missing": _integer(missing.get("any_missing"), "commands.missing.any_missing"),
        "all_present": _integer(missing.get("all_present"), "commands.missing.all_present"),
      },
      "present": {
        "any_missing": _integer(present.get("any_missing"), "commands.present.any_missing"),
        "all_present": _integer(present.get("all_present"), "commands.present.all_present"),
      },
    },
  }


def _missing() -> bool:
  return any(shutil.which(name) is None for name in sys.argv[1:])


def _main(command: Literal["missing", "present"]) -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load command presence configuration: {error}", file=sys.stderr)
    return 2
  result: Literal["any_missing", "all_present"] = "any_missing" if _missing() else "all_present"
  return settings["commands"][command][result]


def missing_main() -> int:
  return _main("missing")


def present_main() -> int:
  return _main("present")
