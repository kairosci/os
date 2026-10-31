from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Editor(TypedDict):
  command: str
  name: str
  glyph: str
  installer: list[str]


class Settings(TypedDict):
  state_home_environment: str
  home_environment: str
  default_state_home: str
  state_relative: str
  encoding: str
  arguments: int
  command_timeout_seconds: int
  stored_value_characters: int
  binary: str
  install_flag: str
  default_command: str
  localization_key: str
  command_missing: list[str]
  launch_installer: list[str]
  notification: list[str]
  localization: list[str]
  legacy_commands: dict[str, str]
  aliases: dict[str, str]
  editors: dict[str, Editor]
  usage: str
  config_error: str
  command_error: str
  success: int
  invalid_arguments: int
  invalid_selection: int
  config_error_status: int
  command_error_status: int


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError()
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError()
  return value


def _integer(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError()
  return value


def _strings(value: object) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError()
  return cast(list[str], value)


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  document = _mapping(yaml.safe_load((root / "data/cli/default-editor.yml").read_text(encoding="utf-8")))
  paths = _mapping(document.get("paths"))
  limits = _mapping(document.get("limits"))
  values = _mapping(document.get("values"))
  commands = _mapping(document.get("commands"))
  legacy = _mapping(document.get("legacy"))
  legacy_commands = _mapping(legacy.get("command_names"))
  aliases = _mapping(document.get("aliases"))
  editors_config = _mapping(document.get("editors"))
  editors: dict[str, Editor] = {}
  for name, raw_editor in editors_config.items():
    editor = _mapping(raw_editor)
    editors[name] = {
      "command": _text(editor.get("command")),
      "name": _text(editor.get("name")),
      "glyph": _text(editor.get("glyph")),
      "installer": _strings(editor.get("installer")),
    }
  messages = _mapping(document.get("messages"))
  statuses = _mapping(document.get("statuses"))
  return {
    "state_home_environment": _text(paths.get("state_home_environment")),
    "home_environment": _text(paths.get("home_environment")),
    "default_state_home": _text(paths.get("default_state_home")),
    "state_relative": _text(paths.get("state_relative")),
    "encoding": _text(paths.get("encoding")),
    "arguments": _integer(limits.get("arguments")),
    "command_timeout_seconds": _integer(limits.get("command_timeout_seconds")),
    "stored_value_characters": _integer(limits.get("stored_value_characters")),
    "binary": _text(values.get("binary")),
    "install_flag": _text(values.get("install_flag")),
    "default_command": _text(values.get("default_command")),
    "localization_key": _text(values.get("localization_key")),
    "command_missing": _strings(commands.get("command_missing")),
    "launch_installer": _strings(commands.get("launch_installer")),
    "notification": _strings(commands.get("notification")),
    "localization": _strings(commands.get("localization")),
    "legacy_commands": {key: _text(value) for key, value in legacy_commands.items()},
    "aliases": {key: _text(value) for key, value in aliases.items()},
    "editors": editors,
    "usage": _text(messages.get("usage")),
    "config_error": _text(messages.get("config_error")),
    "command_error": _text(messages.get("command_error")),
    "success": _integer(statuses.get("success")),
    "invalid_arguments": _integer(statuses.get("invalid_arguments")),
    "invalid_selection": _integer(statuses.get("invalid_selection")),
    "config_error_status": _integer(statuses.get("config_error")),
    "command_error_status": _integer(statuses.get("command_error")),
  }


def _state_path(settings: Settings) -> Path:
  state_home = os.environ.get(settings["state_home_environment"])
  if state_home is None or state_home == "":
    relative = Path(settings["default_state_home"])
    if relative.is_absolute() or ".." in relative.parts:
      raise ValueError()
    root = Path(os.environ[settings["home_environment"]]).joinpath(*relative.parts)
  else:
    root = Path(state_home)
  relative_state = Path(settings["state_relative"])
  if relative_state.is_absolute() or ".." in relative_state.parts:
    raise ValueError()
  return root.joinpath(*relative_state.parts)


def _run(command: list[str], settings: Settings, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    command,
    check=False,
    capture_output=capture,
    text=True,
    timeout=settings["command_timeout_seconds"] if capture else None,
  )


def _read_current(path: Path, settings: Settings) -> str:
  try:
    if path.is_file():
      with path.open(encoding=settings["encoding"]) as stream:
        current = stream.readline(settings["stored_value_characters"] + 1).rstrip("\n")
    else:
      current = ""
  except FileNotFoundError:
    current = ""
  if len(current) > settings["stored_value_characters"]:
    current = ""
  if not current:
    current = settings["default_command"]
  return settings["legacy_commands"].get(current, current)


def _arguments(arguments: list[str], settings: Settings) -> tuple[bool, str | None]:
  installing = bool(arguments and arguments[0] == settings["install_flag"])
  remaining = arguments[1:] if installing else arguments
  if len(remaining) > settings["arguments"]:
    return installing, None
  return installing, remaining[0] if remaining else None


def default_editor_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
    state_path = _state_path(settings)
  except (KeyError, OSError, UnicodeError, ValueError, yaml.YAMLError):
    print("Could not load editor command settings.", file=sys.stderr)
    return 1

  installing, selection = _arguments(arguments, settings)
  if selection is None and (not arguments or installing and len(arguments) == 1):
    try:
      print(_read_current(state_path, settings))
      return settings["success"]
    except (OSError, UnicodeError):
      print(settings["config_error"], file=sys.stderr)
      return settings["config_error_status"]
  if selection is None:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]

  selection = settings["aliases"].get(selection, selection)
  editor = settings["editors"].get(selection)
  if editor is None:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_selection"]

  try:
    missing = _run([*settings["command_missing"], editor["command"]], settings)
    if missing.returncode == settings["success"]:
      if not installing:
        return _run(
          [*settings["launch_installer"], settings["binary"], settings["install_flag"], selection],
          settings,
        ).returncode
      installed = _run(editor["installer"], settings)
      if installed.returncode != settings["success"]:
        return installed.returncode

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(f"{editor['command']}\n", encoding=settings["encoding"])
    localized = _run([*settings["localization"], settings["localization_key"], editor["name"]], settings, capture=True)
    return _run([*settings["notification"], editor["glyph"], localized.stdout.rstrip("\n")], settings).returncode
  except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
    print(settings["command_error"], file=sys.stderr)
    return settings["command_error_status"]
