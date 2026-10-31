from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class DbusSettings(TypedDict):
  command: list[str]
  destination: str
  path: str
  interface: str
  method: str
  signature: str
  urgency_hint: str
  urgency_type: str
  glyph_hint: str
  image_hint: str
  exec_hint: str
  actions_count: int


class Settings(TypedDict):
  timeout_seconds: int
  statuses: dict[str, int]
  defaults: dict[str, object]
  options: dict[str, str]
  boolean_options: list[str]
  urgency: dict[str, int]
  dbus: DbusSettings
  messages: dict[str, str]


class _ArgumentError(ValueError):
  def __init__(self, message: str, *, show_usage: bool = False) -> None:
    super().__init__(message)
    self.show_usage = show_usage


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError("configuration must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError("configuration text must be non-empty")
  return value


def _strings(value: object) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(part, str) and part for part in value):
    raise ValueError("configuration command must be a non-empty list of strings")
  return cast(list[str], value)


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/notification-send.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  statuses = _mapping(document.get("statuses"))
  defaults = _mapping(document.get("defaults"))
  options = _mapping(document.get("options"))
  urgency = _mapping(document.get("urgency"))
  dbus = _mapping(document.get("dbus"))
  messages = _mapping(document.get("messages"))
  timeout = document.get("timeout_seconds")
  booleans = document.get("boolean_options")
  if type(timeout) is not int or timeout <= 0:
    raise ValueError("timeout_seconds must be a positive integer")
  if not isinstance(booleans, list) or not all(isinstance(value, str) for value in booleans):
    raise ValueError("boolean_options must be a list of strings")
  parsed_statuses = {key: value for key, value in statuses.items() if type(value) is int and value > 0}
  if len(parsed_statuses) != len(statuses):
    raise ValueError("statuses must contain positive integers")
  parsed_options = {key: _text(value) for key, value in options.items()}
  parsed_urgency = {key: value for key, value in urgency.items() if type(value) is int and 0 <= value <= 255}
  if len(parsed_urgency) != len(urgency) or not parsed_urgency:
    raise ValueError("urgency values must be bytes")
  actions_count = dbus.get("actions_count")
  if type(actions_count) is not int or actions_count < 0:
    raise ValueError("actions_count must be a non-negative integer")
  parsed_dbus: DbusSettings = {
    "command": _strings(dbus.get("command")),
    "destination": _text(dbus.get("destination")),
    "path": _text(dbus.get("path")),
    "interface": _text(dbus.get("interface")),
    "method": _text(dbus.get("method")),
    "signature": _text(dbus.get("signature")),
    "urgency_hint": _text(dbus.get("urgency_hint")),
    "urgency_type": _text(dbus.get("urgency_type")),
    "glyph_hint": _text(dbus.get("glyph_hint")),
    "image_hint": _text(dbus.get("image_hint")),
    "exec_hint": _text(dbus.get("exec_hint")),
    "actions_count": actions_count,
  }
  return {
    "timeout_seconds": timeout,
    "statuses": parsed_statuses,
    "defaults": defaults,
    "options": parsed_options,
    "boolean_options": cast(list[str], booleans),
    "urgency": cast(dict[str, int], parsed_urgency),
    "dbus": parsed_dbus,
    "messages": {key: _text(value) for key, value in messages.items()},
  }


def _format(settings: Settings, key: str, **values: str) -> str:
  return settings["messages"][key].format(**values)


def _known_flag(settings: Settings, token: str) -> bool:
  option = token.split("=", 1)[0]
  return option in settings["options"] or token == "--exec"


def _parse_option(settings: Settings, arguments: list[str]) -> tuple[bool, int, str, object]:
  token = arguments[0]
  if token.startswith("--") and "=" in token:
    option, value = token.split("=", 1)
    consumed = 1
  else:
    option = token
    value = arguments[1] if len(arguments) > 1 else ""
    consumed = 2
  destination = settings["options"].get(option)
  if destination is None:
    return False, 0, "", ""
  if destination in settings["boolean_options"]:
    if "=" in token:
      return True, 1, destination, value.lower() in ("1", "true", "yes")
    return True, 1, destination, True
  if consumed == 2 and len(arguments) < 2:
    raise _ArgumentError(_format(settings, "missing_value", option=option), show_usage=True)
  if destination in ("replaces_id", "expire_timeout"):
    pattern = r"[0-9]+" if destination == "replaces_id" else r"-?[0-9]+"
    if re.fullmatch(pattern, value) is None:
      expected = "numeric id" if destination == "replaces_id" else "milliseconds"
      raise _ArgumentError(_format(settings, "invalid_numeric", option=option, expected=expected, value=value))
    value = int(value)
  return True, consumed, destination, value


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  values = dict(settings["defaults"])
  remaining = list(arguments)
  try:
    while remaining:
      parsed, consumed, destination, value = _parse_option(settings, remaining)
      if not parsed:
        break
      values[destination] = value
      del remaining[:consumed]
    if not remaining:
      print(_format(settings, "usage"), file=sys.stderr)
      return settings["statuses"]["usage"]
    headline = remaining.pop(0)
    description = ""
    if remaining and not _known_flag(settings, remaining[0]):
      description = remaining.pop(0)
    exec_args: list[str] | None = None
    while remaining:
      if remaining[0] == "--exec":
        exec_args = remaining[1:]
        remaining.clear()
        break
      parsed, consumed, destination, value = _parse_option(settings, remaining)
      if not parsed:
        raise _ArgumentError(_format(settings, "unknown_option", option=remaining[0]), show_usage=True)
      values[destination] = value
      del remaining[:consumed]
  except _ArgumentError as error:
    print(error, file=sys.stderr)
    if error.show_usage:
      print(_format(settings, "usage"), file=sys.stderr)
    return settings["statuses"]["invalid"]

  urgency = str(values["urgency"])
  if urgency not in settings["urgency"]:
    print(_format(settings, "urgency", value=urgency), file=sys.stderr)
    return settings["statuses"]["invalid"]

  hints = [settings["dbus"]["urgency_hint"], settings["dbus"]["urgency_type"], str(settings["urgency"][urgency])]
  if values["glyph"]:
    hints.extend([settings["dbus"]["glyph_hint"], "s", str(values["glyph"])])
  if values["image"]:
    hints.extend([settings["dbus"]["image_hint"], "s", str(values["image"])])
  if exec_args is not None:
    if not exec_args or not exec_args[0]:
      print(_format(settings, "exec_missing"), file=sys.stderr)
      return settings["statuses"]["invalid"]
    if len(exec_args) == 1 and any(character.isspace() for character in exec_args[0]):
      print(_format(settings, "exec_whole_command"), file=sys.stderr)
      print(_format(settings, "exec_whole_command_hint"), file=sys.stderr)
      return settings["statuses"]["invalid"]
    hints.extend([settings["dbus"]["exec_hint"], "s", json.dumps(exec_args, ensure_ascii=False, separators=(",", ":"))])

  dbus = settings["dbus"]
  command = dbus["command"] + [
    dbus["destination"], dbus["path"], dbus["interface"], dbus["method"], dbus["signature"],
    str(values["app_name"]), str(values["replaces_id"]), str(values["app_icon"]), headline, description,
    str(dbus["actions_count"]), str(len(hints) // 3), *hints, str(values["expire_timeout"]),
  ]
  try:
    result = subprocess.run(
      command,
      check=False,
      stdout=subprocess.PIPE if values["print_id"] else subprocess.DEVNULL,
      text=True,
      timeout=settings["timeout_seconds"],
    )
  except subprocess.TimeoutExpired:
    print(_format(settings, "timeout"), file=sys.stderr)
    return settings["statuses"]["timeout"]
  except OSError:
    print(_format(settings, "command_error"), file=sys.stderr)
    return settings["statuses"]["command_error"]
  if values["print_id"] and result.returncode == 0:
    print(result.stdout.rstrip("\n").rsplit(" ", 1)[-1])
  return result.returncode
