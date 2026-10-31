from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  grep: list[str]
  product_paths: list[str]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid hardware match configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid hardware match configuration: {label} must be a non-empty string")
  return value


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(
    isinstance(item, str) and item for item in value
  ):
    raise ValueError(f"invalid hardware match configuration: {label} must be a list of strings")
  return cast(list[str], value)


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-match.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  commands = _mapping(document.get("commands"), "commands")
  paths = _mapping(document.get("paths"), "paths")
  return {
    "grep": _strings(commands.get("grep"), "commands.grep"),
    "product_paths": [
      _text(paths.get("dmi_product_name"), "paths.dmi_product_name"),
      _text(paths.get("dmi_product_family"), "paths.dmi_product_family"),
    ],
  }


def match_main(arguments: list[str]) -> int:
  if arguments and arguments[0] == "--":
    arguments = arguments[1:]
  try:
    settings = _settings()
    pattern = arguments[0] if arguments else ""
    return_code = 1
    for product_path in settings["product_paths"]:
      try:
        result = subprocess.run(
          [*settings["grep"], pattern, product_path],
          check=False,
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
        )
      except OSError:
        return 127
      if result.returncode == 0:
        return 0
      return_code = result.returncode
    return return_code
  except (KeyError, OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG
