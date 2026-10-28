from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, TypeGuard

import yaml


class LanguageSetup(TypedDict):
  marker_environment: str
  marker_default: str
  fallback_marker: str
  locales_file_environment: str
  locales_file_default: str
  code_pattern: str
  language_environment: str
  default_language: str
  generator_command: list[str]
  messages: dict[str, dict[str, str]]


def _is_string_mapping(value: object) -> TypeGuard[dict[str, str]]:
  return isinstance(value, dict) and all(
    isinstance(key, str) and isinstance(item, str) for key, item in value.items()
  )


def _is_language_setup(value: object) -> TypeGuard[LanguageSetup]:
  if not isinstance(value, dict):
    return False
  text_fields = (
    "marker_environment", "marker_default", "fallback_marker", "locales_file_environment",
    "locales_file_default", "code_pattern", "language_environment", "default_language",
  )
  messages = value.get("messages")
  return (
    all(isinstance(value.get(field), str) for field in text_fields)
    and isinstance(value.get("generator_command"), list)
    and all(isinstance(part, str) for part in value["generator_command"])
    and isinstance(messages, dict)
    and all(isinstance(language, str) and _is_string_mapping(catalog) for language, catalog in messages.items())
    and isinstance(messages.get("en"), dict)
  )


def _messages(settings: LanguageSetup, code: str) -> dict[str, str]:
  default = settings["default_language"]
  for source in (code, os.environ.get(settings["language_environment"], "")):
    language = source.split("-", 1)[0].split("_", 1)[0].lower()
    if language in settings["messages"]:
      return settings["messages"][language]
  return settings["messages"][default]


def main() -> int:
  root = Path(os.environ["AP"])
  config: object = yaml.safe_load((root / "data/installer/system-setup.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid system setup configuration")
  settings = config["language_setup"]
  if not _is_language_setup(settings):
    raise ValueError("invalid language setup configuration")
  marker = Path(os.environ.get(settings["marker_environment"]) or settings["marker_default"])
  try:
    code = marker.read_text(encoding="utf-8").splitlines()[0]
  except OSError:
    marker = Path(settings["fallback_marker"])
    try:
      code = marker.read_text(encoding="utf-8").splitlines()[0]
    except OSError:
      return 0
    except IndexError:
      return 0
  except IndexError:
    return 0
  if not code:
    return 0

  locales_path = Path(
    os.environ.get(settings["locales_file_environment"]) or root / settings["locales_file_default"]
  )
  try:
    locales = json.loads(locales_path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError):
    return 1
  if not _is_string_mapping(locales):
    return 1
  if re.fullmatch(settings["code_pattern"], code) is None or code not in locales:
    message = _messages(settings, code)["invalid"].format(marker=marker, code=code)
    print(message, file=sys.stderr)
    return 0

  command = [part.format(ap=root) for part in settings["generator_command"]]
  return subprocess.run([*command, code], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
