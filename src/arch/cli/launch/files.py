from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Launcher(TypedDict):
  command: list[str]
  working_directory: list[str]


class Statuses(TypedDict):
  configuration_error: int
  command_error: int
  timeout: int


class Settings(TypedDict):
  launchers: dict[str, Launcher]
  working_directory_timeout: int
  statuses: Statuses
  command_error_message: str
  timeout_message: str


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"{label} must be a non-empty argv list")
  return cast(list[str], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"{label} must be non-empty text")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise ValueError(f"{label} must be an exit status")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/launch-files.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "configuration")
  raw_launchers = _mapping(document.get("launchers"), "launchers")
  launchers: dict[str, Launcher] = {}
  for name, raw_launcher in raw_launchers.items():
    values = _mapping(raw_launcher, name)
    command = _strings(values.get("command"), f"{name}.command")
    directory_command = values.get("working_directory")
    if directory_command is None:
      directory_command = []
    elif not isinstance(directory_command, list) or not directory_command or not all(
      isinstance(item, str) and item for item in directory_command
    ):
      raise ValueError(f"{name}.working_directory must be a non-empty argv list")
    launchers[name] = {"command": command, "working_directory": cast(list[str], directory_command)}
  timeouts = _mapping(document.get("timeouts"), "timeouts")
  directory_timeout = timeouts.get("working_directory_seconds")
  if type(directory_timeout) is not int or directory_timeout <= 0:
    raise ValueError("timeouts.working_directory_seconds must be positive")
  raw_statuses = _mapping(document.get("statuses"), "statuses")
  messages = _mapping(document.get("messages"), "messages")
  return {
    "launchers": launchers,
    "working_directory_timeout": directory_timeout,
    "statuses": {
      "configuration_error": _status(raw_statuses.get("configuration_error"), "configuration_error"),
      "command_error": _status(raw_statuses.get("command_error"), "command_error"),
      "timeout": _status(raw_statuses.get("timeout"), "timeout"),
    },
    "command_error_message": _text(messages.get("command_error"), "messages.command_error"),
    "timeout_message": _text(messages.get("timeout"), "messages.timeout"),
  }


def main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  launcher = settings["launchers"].get(Path(sys.argv[0]).name)
  if launcher is None:
    print("Unknown Files launcher", file=sys.stderr)
    return settings["statuses"]["configuration_error"]

  command = launcher["command"]
  directory_command = launcher["working_directory"]
  if directory_command:
    try:
      result = subprocess.run(
        directory_command,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="surrogateescape",
        timeout=settings["working_directory_timeout"],
      )
    except subprocess.TimeoutExpired:
      print(settings["timeout_message"], file=sys.stderr)
      return settings["statuses"]["timeout"]
    except OSError:
      print(settings["command_error_message"], file=sys.stderr)
      return settings["statuses"]["command_error"]
    directory = result.stdout.rstrip("\n")
    if directory:
      command = [*command, directory]

  try:
    os.execvpe(command[0], command, os.environ)
  except OSError:
    print(settings["command_error_message"], file=sys.stderr)
    return settings["statuses"]["command_error"]
