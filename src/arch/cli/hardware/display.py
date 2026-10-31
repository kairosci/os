from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Paths(TypedDict):
  backlight_default: str
  backlight_environment: str
  platform_displays_default: str
  platform_displays_environment: str
  encoding: str


class Directives(TypedDict):
  fields: int
  skip: str
  prefer: str


class Identifiers(TypedDict):
  excluded_names: list[str]
  first_priority: str
  later_priority_patterns: list[str]
  path_separator: str
  dot_name: str
  parent_name: str
  hidden_prefix: str


class Limits(TypedDict):
  platform_config_bytes: int
  backlight_devices: int


class Statuses(TypedDict):
  found: int
  not_found: int
  invalid_configuration: int


class Settings(TypedDict):
  paths: Paths
  directives: Directives
  identifiers: Identifiers
  limits: Limits
  statuses: Statuses


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError()
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError()
  return value


def _text_list(value: object) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
    raise ValueError()
  return cast(list[str], value)


def _positive_integer(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
    raise ValueError()
  return value


def _nonnegative_integer(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError()
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw = yaml.safe_load((root / "data/cli/hardware-display.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  raw_paths = _mapping(document.get("paths"))
  raw_directives = _mapping(document.get("directives"))
  raw_identifiers = _mapping(document.get("identifiers"))
  raw_limits = _mapping(document.get("limits"))
  raw_statuses = _mapping(document.get("statuses"))
  paths: Paths = {
    "backlight_default": _text(raw_paths.get("backlight_default")),
    "backlight_environment": _text(raw_paths.get("backlight_environment")),
    "platform_displays_default": _text(raw_paths.get("platform_displays_default")),
    "platform_displays_environment": _text(raw_paths.get("platform_displays_environment")),
    "encoding": _text(raw_paths.get("encoding")),
  }
  directives: Directives = {
    "fields": _positive_integer(raw_directives.get("fields")),
    "skip": _text(raw_directives.get("skip")),
    "prefer": _text(raw_directives.get("prefer")),
  }
  identifiers: Identifiers = {
    "excluded_names": _text_list(raw_identifiers.get("excluded_names")),
    "first_priority": _text(raw_identifiers.get("first_priority")),
    "later_priority_patterns": _text_list(raw_identifiers.get("later_priority_patterns")),
    "path_separator": _text(raw_identifiers.get("path_separator")),
    "dot_name": _text(raw_identifiers.get("dot_name")),
    "parent_name": _text(raw_identifiers.get("parent_name")),
    "hidden_prefix": _text(raw_identifiers.get("hidden_prefix")),
  }
  limits: Limits = {
    "platform_config_bytes": _positive_integer(raw_limits.get("platform_config_bytes")),
    "backlight_devices": _positive_integer(raw_limits.get("backlight_devices")),
  }
  statuses: Statuses = {
    "found": _nonnegative_integer(raw_statuses.get("found")),
    "not_found": _nonnegative_integer(raw_statuses.get("not_found")),
    "invalid_configuration": _positive_integer(raw_statuses.get("invalid_configuration")),
  }
  if len(set(statuses.values())) != len(statuses):
    raise ValueError()
  return {"paths": paths, "directives": directives, "identifiers": identifiers, "limits": limits, "statuses": statuses}


def _platform_hints(settings: Settings) -> tuple[list[str], list[str]]:
  paths = settings["paths"]
  manifest = Path(os.environ.get(paths["platform_displays_environment"], paths["platform_displays_default"]))
  try:
    with manifest.open(encoding=paths["encoding"], errors="replace") as stream:
      contents = stream.read(settings["limits"]["platform_config_bytes"] + 1)
  except OSError:
    return [], []
  if len(contents.encode(paths["encoding"], errors="replace")) > settings["limits"]["platform_config_bytes"]:
    return [], []

  skips: list[str] = []
  preferences: list[str] = []
  directives = settings["directives"]
  identifiers = settings["identifiers"]
  for line in contents.splitlines():
    fields = line.split()
    if len(fields) != directives["fields"]:
      continue
    directive, name = fields
    if (
      identifiers["path_separator"] in name
      or name in {identifiers["dot_name"], identifiers["parent_name"]}
    ):
      continue
    if directive == directives["skip"]:
      skips.append(name)
    elif directive == directives["prefer"]:
      preferences.append(name)
  return skips, preferences


def _usable(name: str, skips: list[str], settings: Settings) -> bool:
  identifiers = settings["identifiers"]
  if name.startswith(identifiers["hidden_prefix"]) or name in identifiers["excluded_names"]:
    return False
  return not any(fnmatch.fnmatchcase(name, pattern) for pattern in skips)


def _select_device(root: Path, settings: Settings) -> str:
  try:
    names: list[str] = []
    for item in root.iterdir():
      if item.name.startswith(settings["identifiers"]["hidden_prefix"]):
        continue
      if len(names) >= settings["limits"]["backlight_devices"]:
        return ""
      names.append(item.name)
  except OSError:
    return ""
  names.sort()
  skips, preferences = _platform_hints(settings)
  usable_names = [name for name in names if _usable(name, skips, settings)]
  if not usable_names:
    return ""

  identifiers = settings["identifiers"]
  usable_present = {
    name for name in usable_names if (root / name).exists()
  }
  if identifiers["first_priority"] in usable_present:
    return identifiers["first_priority"]
  if preferences:
    preferred = next((name for name in preferences if name in usable_present), "")
    if preferred:
      return preferred
  for pattern in identifiers["later_priority_patterns"]:
    candidate = next((name for name in usable_names if name in usable_present and fnmatch.fnmatchcase(name, pattern)), "")
    if candidate:
      return candidate
  return usable_names[0]


def display_main() -> int:
  try:
    settings = _settings()
    paths = settings["paths"]
    root = Path(os.environ.get(paths["backlight_environment"], paths["backlight_default"]))
    device = _select_device(root, settings)
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return os.EX_CONFIG
  if not device:
    return settings["statuses"]["not_found"]
  print(device)
  return settings["statuses"]["found"]
