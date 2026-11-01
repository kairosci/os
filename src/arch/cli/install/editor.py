from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  install_package: list[str]
  launch_application: list[str]
  configuration_error: str
  operation_error: str
  installing: str
  success: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"Zed installer {label} must be a mapping")
  return cast(dict[str, object], value)


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
    raise TypeError(f"Zed installer {label} must be a non-empty string list")
  return cast(list[str], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"Zed installer {label} must be a non-empty string")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"Zed installer {label} must be an exit status")
  return value


def _settings(document: dict[str, object]) -> Settings:
  commands = _mapping(document.get("commands"), "commands")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  return {
    "install_package": _strings(commands.get("install_package"), "package command"),
    "launch_application": _strings(commands.get("launch_application"), "launch command"),
    "configuration_error": _text(messages.get("configuration_error"), "configuration error message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "installing": _text(messages.get("installing"), "progress message"),
    "success": _status(statuses.get("success"), "success status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
  }


def zed_main() -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load((root / "data/cli/install-editor-zed.yml").read_text(encoding="utf-8"))
    document = _mapping(raw, "configuration")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"), "configuration error message")
    settings = _settings(document)
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    if configuration_error:
      print(configuration_error.format(error=error), file=sys.stderr)
    else:
      print(error, file=sys.stderr)
    return 1

  print(settings["installing"], flush=True)
  try:
    result = subprocess.run(settings["install_package"], check=False)
    if result.returncode != settings["success"]:
      return result.returncode
    subprocess.Popen(
      settings["launch_application"],
      stdin=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      start_new_session=True,
    )
  except (OSError, subprocess.SubprocessError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
