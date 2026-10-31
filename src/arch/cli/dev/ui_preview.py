from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  command: list[str]
  payload_key: str
  default_payload: str
  maximum_section_length: int
  messages: dict[str, str]
  statuses: dict[str, int]


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"{label} must be non-empty text")
  return value


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
    raise ValueError(f"{label} must be a non-empty string list")
  return cast(list[str], value)


def _integer(value: object, label: str) -> int:
  if type(value) is not int:
    raise ValueError(f"{label} must be an integer")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw = yaml.safe_load((root / "data/cli/dev-ui-preview.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "configuration")
  raw_messages = _mapping(config.get("messages"), "messages")
  raw_statuses = _mapping(config.get("statuses"), "statuses")
  messages = {key: _text(value, f"messages.{key}") for key, value in raw_messages.items()}
  statuses = {key: _integer(value, f"statuses.{key}") for key, value in raw_statuses.items()}
  if set(messages) != {"invalid_arguments", "section_too_long", "command_error"}:
    raise ValueError("messages must define every gallery diagnostic")
  if set(statuses) != {
    "success", "invalid_arguments", "command_error", "signal_status_base"
  } or statuses["success"] != 0 or any(
    not 0 < value <= 255 for key, value in statuses.items() if key != "success"
  ):
    raise ValueError("statuses must define valid gallery exit codes")
  maximum_section_length = _integer(config.get("maximum_section_length"), "maximum_section_length")
  if maximum_section_length <= 0:
    raise ValueError("maximum_section_length must be positive")
  default_payload = _text(config.get("default_payload"), "default_payload")
  if not isinstance(json.loads(default_payload), dict):
    raise TypeError("default_payload must be a JSON object")
  return {
    "command": _strings(config.get("command"), "command"),
    "payload_key": _text(config.get("payload_key"), "payload_key"),
    "default_payload": default_payload,
    "maximum_section_length": maximum_section_length,
    "messages": messages,
    "statuses": statuses,
  }


def main(arguments: list[str] | None = None) -> int:
  settings = _settings()
  args = sys.argv[1:] if arguments is None else arguments
  if len(args) > 1:
    print(settings["messages"]["invalid_arguments"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]

  payload = settings["default_payload"]
  if args and args[0]:
    if len(args[0]) > settings["maximum_section_length"]:
      print(settings["messages"]["section_too_long"], file=sys.stderr)
      return settings["statuses"]["invalid_arguments"]
    payload = json.dumps({settings["payload_key"]: args[0]}, separators=(",", ":"))

  try:
    result = subprocess.run([*settings["command"], payload], check=False)
  except OSError:
    print(settings["messages"]["command_error"], file=sys.stderr)
    return settings["statuses"]["command_error"]
  if result.returncode < 0:
    return settings["statuses"]["signal_status_base"] + -result.returncode
  return result.returncode
