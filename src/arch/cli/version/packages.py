from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from typing import TypedDict

import yaml


class Log(TypedDict):
  path_environment: str
  default_path: str
  match_text: str
  timestamp_pattern: str
  timestamp_group: int


class Commands(TypedDict):
  locale: list[str]
  date: list[str]
  default_language: str
  date_formats: dict[str, str]


class PackageVersionConfig(TypedDict):
  commands: Commands
  log: Log


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid package version configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid package version configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid package version configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid package version configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _text_mapping(value: object, label: str) -> dict[str, str]:
  mapping = _mapping(value, label)
  return {
    _text(key, f"{label} key"): _text(item, f"{label} value")
    for key, item in mapping.items()
  }


def _settings() -> PackageVersionConfig:
  root = Path(os.environ["ARCH_PATH"])
  raw: object = yaml.safe_load((root / "data/cli/version-pkgs.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  commands = _mapping(settings.get("commands"), "commands")
  log = _mapping(settings.get("log"), "log")
  return {
    "commands": {
      "locale": _text_list(commands.get("locale"), "commands.locale"),
      "date": _text_list(commands.get("date"), "commands.date"),
      "default_language": _text(commands.get("default_language"), "commands.default_language"),
      "date_formats": _text_mapping(commands.get("date_formats"), "commands.date_formats"),
    },
    "log": {
      "path_environment": _text(log.get("path_environment"), "log.path_environment"),
      "default_path": _text(log.get("default_path"), "log.default_path"),
      "match_text": _text(log.get("match_text"), "log.match_text"),
      "timestamp_pattern": _text(log.get("timestamp_pattern"), "log.timestamp_pattern"),
      "timestamp_group": _integer(log.get("timestamp_group"), "log.timestamp_group"),
    },
  }


def _report(settings: PackageVersionConfig) -> int:
  log = settings["log"]
  path = Path(os.environ.get(log["path_environment"]) or log["default_path"])
  try:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
  except OSError:
    lines = []

  matching = [line for line in lines if log["match_text"] in line]
  latest = matching[-1] if matching else ""
  timestamp = latest
  match = re.search(log["timestamp_pattern"], latest)
  if match:
    timestamp = match.group(int(log["timestamp_group"]))

  locale_result = subprocess.run(settings["commands"]["locale"], check=False, stdout=subprocess.PIPE, text=True)
  locale_name = locale_result.stdout.rstrip("\n")
  language = locale_name.split(".", 1)[0].split("_", 1)[0]
  date_format = settings["commands"]["date_formats"].get(
    language,
    settings["commands"]["date_formats"][settings["commands"]["default_language"]],
  )
  environment = os.environ.copy()
  environment["LC_TIME"] = locale_name
  command = [argument.format(timestamp=timestamp, format=date_format) for argument in settings["commands"]["date"]]
  result = subprocess.run(command, check=False, env=environment)
  return result.returncode


def main() -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load package version configuration: {error}", file=sys.stderr)
    return 2
  try:
    return _report(settings)
  except (IndexError, KeyError, OSError, re.error, subprocess.SubprocessError, ValueError) as error:
    print(f"Could not report package upgrade date: {error}", file=sys.stderr)
    return 2
