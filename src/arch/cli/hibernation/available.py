from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  swap_table: Path
  image_size: Path
  resume_config: Path
  swap_size_bytes_per_unit: int
  swap_size_column: int
  swap_header_lines: int
  excluded_swap_name_fragments: list[str]
  available_status: int
  unavailable_status: int


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError("configuration must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hibernation-available.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  paths = _mapping(document.get("paths"))
  statuses = _mapping(document.get("statuses"))
  unit = document.get("swap_size_bytes_per_unit")
  size_column = document.get("swap_size_column")
  header_lines = document.get("swap_header_lines")
  excluded_names = document.get("excluded_swap_name_fragments")
  available = statuses.get("available")
  unavailable = statuses.get("unavailable")
  if type(unit) is not int or unit <= 0:
    raise ValueError("swap_size_bytes_per_unit must be a positive integer")
  if type(size_column) is not int or size_column < 0 or type(header_lines) is not int or header_lines < 0:
    raise ValueError("swap table columns and header count must be non-negative integers")
  if not isinstance(excluded_names, list) or not all(isinstance(value, str) and value for value in excluded_names):
    raise ValueError("excluded_swap_name_fragments must be a list of non-empty strings")
  if type(available) is not int or available != 0 or type(unavailable) is not int or unavailable == 0:
    raise ValueError("statuses must define zero for available and non-zero for unavailable")
  return {
    "swap_table": Path(_text(paths.get("swaps"))),
    "image_size": Path(_text(paths.get("image_size"))),
    "resume_config": Path(_text(paths.get("resume_config"))),
    "swap_size_bytes_per_unit": unit,
    "swap_size_column": size_column,
    "swap_header_lines": header_lines,
    "excluded_swap_name_fragments": cast(list[str], excluded_names),
    "available_status": available,
    "unavailable_status": unavailable,
  }


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError("path configuration must be a non-empty string")
  return value


def _swap_bytes(table: Path, unit: int, size_column: int, header_lines: int, excluded_names: list[str]) -> int:
  total = 0
  for line in table.read_text(encoding="utf-8").splitlines()[header_lines:]:
    fields = line.split()
    if len(fields) <= size_column or any(fragment in fields[0] for fragment in excluded_names):
      continue
    try:
      total += int(fields[size_column]) * unit
    except ValueError:
      continue
  return total


def main() -> int:
  try:
    settings = _settings()
    image_size = int(settings["image_size"].read_text(encoding="ascii").strip())
    swap_size = _swap_bytes(
      settings["swap_table"],
      settings["swap_size_bytes_per_unit"],
      settings["swap_size_column"],
      settings["swap_header_lines"],
      settings["excluded_swap_name_fragments"],
    )
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return 1
  if swap_size > image_size and settings["resume_config"].is_file():
    return settings["available_status"]
  return settings["unavailable_status"]
