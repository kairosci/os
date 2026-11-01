from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml

from arch.cli.chromium.features import ensure_chromium_flags
from arch.cli.chromium.features import load_settings as load_chromium_feature_settings


class Settings(TypedDict):
  hardware_check: list[str]
  chromium_feature: str
  configuration_error: str
  operation_error: str
  success: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"camera setup {label} must be a mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"camera setup {label} must be non-empty text")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"camera setup {label} must be an exit status")
  return value


def _settings(document: dict[str, object]) -> Settings:
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  hardware_check = document.get("hardware_check")
  if not isinstance(hardware_check, list) or not hardware_check or not all(
    isinstance(part, str) and part for part in hardware_check
  ):
    raise TypeError("camera setup hardware check must be a non-empty argument list")
  return {
    "hardware_check": cast(list[str], hardware_check),
    "chromium_feature": _text(document.get("chromium_feature"), "Chromium feature"),
    "configuration_error": _text(messages.get("configuration_error"), "configuration error message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "success": _status(statuses.get("success"), "success status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
  }


def install_camera_main() -> int:
  configuration_error: str | None = None
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load((root / "data/cli/install-camera.yml").read_text(encoding="utf-8"))
    document = _mapping(raw, "configuration")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"), "configuration error message")
    settings = _settings(document)
  except (KeyError, OSError, RuntimeError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(configuration_error.format(error=error) if configuration_error is not None else error, file=sys.stderr)
    return 1

  try:
    hardware = subprocess.run(settings["hardware_check"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if hardware.returncode != 0:
      return settings["success"]
    home = Path(os.environ["HOME"]).resolve(strict=True)
    feature_settings = load_chromium_feature_settings(root)
    ensure_chromium_flags(home, feature_settings, settings["chromium_feature"])
  except (KeyError, OSError, RuntimeError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
