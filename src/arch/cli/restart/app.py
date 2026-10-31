"""Restart an application through the user session launcher."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class RestartSettings(TypedDict):
  minimum_arguments: int
  stop_timeout_seconds: int
  stop_application: list[str]
  launch_application: list[str]
  output_discard: str
  hyprsunset: str
  usage: str
  launch_error: str
  success: int
  invalid_arguments: int
  operation_failed: int


def _mapping(value: object, error_message: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(error_message)
  return cast(dict[str, object], value)


def _text(value: object, error_message: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(error_message)
  return value


def _strings(value: object, error_message: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(error_message)
  return cast(list[str], value)


def _integer(value: object, error_message: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError(error_message)
  return value


def _positive_integer(value: object, error_message: str) -> int:
  result = _integer(value, error_message)
  if result == 0:
    raise ValueError(error_message)
  return result


def _settings() -> RestartSettings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/restart-app.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise TypeError()
  raw_messages = raw.get("messages")
  if not isinstance(raw_messages, dict):
    raise TypeError()
  configuration_error = raw_messages.get("configuration_error")
  if not isinstance(configuration_error, str) or not configuration_error:
    raise ValueError()
  document = _mapping(raw, configuration_error)
  limits = _mapping(document.get("limits"), configuration_error)
  commands = _mapping(document.get("commands"), configuration_error)
  paths = _mapping(document.get("paths"), configuration_error)
  applications = _mapping(document.get("applications"), configuration_error)
  messages = _mapping(document.get("messages"), configuration_error)
  statuses = _mapping(document.get("statuses"), configuration_error)
  return {
    "minimum_arguments": _positive_integer(limits.get("minimum_arguments"), configuration_error),
    "stop_timeout_seconds": _positive_integer(limits.get("stop_timeout_seconds"), configuration_error),
    "stop_application": _strings(commands.get("stop_application"), configuration_error),
    "launch_application": _strings(commands.get("launch_application"), configuration_error),
    "output_discard": _text(paths.get("output_discard"), configuration_error),
    "hyprsunset": _text(applications.get("hyprsunset"), configuration_error),
    "usage": _text(messages.get("usage"), configuration_error),
    "launch_error": _text(messages.get("launch_error"), configuration_error),
    "success": _integer(statuses.get("success"), configuration_error),
    "invalid_arguments": _integer(statuses.get("invalid_arguments"), configuration_error),
    "operation_failed": _integer(statuses.get("operation_failed"), configuration_error),
  }


def _load_settings() -> RestartSettings | None:
  try:
    return _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"{error}", file=sys.stderr)
    return None


def _restart(arguments: list[str], settings: RestartSettings) -> int:
  if len(arguments) < settings["minimum_arguments"] or not arguments[0]:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]
  try:
    subprocess.run(
      [*settings["stop_application"], arguments[0]],
      check=False,
      timeout=settings["stop_timeout_seconds"],
    )
    with open(settings["output_discard"], "wb") as output:
      subprocess.Popen(
        [*settings["launch_application"], *arguments],
        stdout=output,
        stderr=output,
      )
  except (OSError, subprocess.SubprocessError) as error:
    print(f"{settings['launch_error']}: {error}", file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]


def restart_app_main(arguments: list[str]) -> int:
  settings = _load_settings()
  if settings is None:
    return 1
  return _restart(arguments, settings)


def restart_hyprsunset_main() -> int:
  settings = _load_settings()
  if settings is None:
    return 1
  return _restart([settings["hyprsunset"]], settings)
