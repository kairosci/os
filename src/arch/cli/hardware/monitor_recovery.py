from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Paths(TypedDict):
  home_environment: str
  toggle_relative: str
  parent_component: str


class Commands(TypedDict):
  external_monitor_status: list[str]


class Statuses(TypedDict):
  success: int
  configuration_error: int


class Settings(TypedDict):
  paths: Paths
  commands: Commands
  statuses: Statuses


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError()
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError()
  return value


def _command(value: object) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError()
  return cast(list[str], value)


def _status(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError()
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw = yaml.safe_load((root / "data/cli/hardware-monitor-recovery.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  raw_paths = _mapping(document.get("paths"))
  raw_commands = _mapping(document.get("commands"))
  raw_statuses = _mapping(document.get("statuses"))
  return {
    "paths": {
      "home_environment": _text(raw_paths.get("home_environment")),
      "toggle_relative": _text(raw_paths.get("toggle_relative")),
      "parent_component": _text(raw_paths.get("parent_component")),
    },
    "commands": {
      "external_monitor_status": _command(raw_commands.get("external_monitor_status")),
    },
    "statuses": {
      "success": _status(raw_statuses.get("success")),
      "configuration_error": _status(raw_statuses.get("configuration_error")),
    },
  }


def recover_internal_monitor_main() -> int:
  try:
    settings = _settings()
    paths = settings["paths"]
    home = Path(os.environ[paths["home_environment"]])
    relative = Path(paths["toggle_relative"])
    if relative.is_absolute() or not relative.parts or paths["parent_component"] in relative.parts:
      return settings["statuses"]["configuration_error"]
    toggle = home.joinpath(*relative.parts)
    if not toggle.is_file():
      return settings["statuses"]["success"]
    result = subprocess.run(settings["commands"]["external_monitor_status"], check=False)
    if result.returncode == settings["statuses"]["success"]:
      return settings["statuses"]["success"]
    toggle.unlink(missing_ok=True)
    return settings["statuses"]["success"]
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return os.EX_CONFIG
