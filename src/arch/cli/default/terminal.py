from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class App(TypedDict):
  command: str
  desktop_id: str
  name: str
  glyph: str
  installer: list[str]


class Settings(TypedDict):
  config_home_environment: str
  home_environment: str
  default_config_home: str
  config_relative: str
  encoding: str
  arguments: int
  command_timeout_seconds: int
  binary: str
  install_flag: str
  localization_key: str
  config_content: str
  read_default: list[str]
  command_missing: list[str]
  launch_installer: list[str]
  notification: list[str]
  localization: list[str]
  apps: dict[str, App]
  usage: str
  command_error: str
  success: int
  invalid_arguments: int
  invalid_selection: int
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
  document = _mapping(yaml.safe_load((root / "data/cli/default-terminal.yml").read_text(encoding="utf-8")))
  paths = _mapping(document.get("paths"))
  limits = _mapping(document.get("limits"))
  values = _mapping(document.get("values"))
  commands = _mapping(document.get("commands"))
  apps_config = _mapping(document.get("apps"))
  apps: dict[str, App] = {}
  for name, raw_app in apps_config.items():
    app = _mapping(raw_app)
    apps[name] = {
      "command": _text(app.get("command")),
      "desktop_id": _text(app.get("desktop_id")),
      "name": _text(app.get("name")),
      "glyph": _text(app.get("glyph")),
      "installer": _strings(app.get("installer")),
    }
  messages = _mapping(document.get("messages"))
  statuses = _mapping(document.get("statuses"))
  return {
    "config_home_environment": _text(paths.get("config_home_environment")),
    "home_environment": _text(paths.get("home_environment")),
    "default_config_home": _text(paths.get("default_config_home")),
    "config_relative": _text(paths.get("config_relative")),
    "encoding": _text(paths.get("encoding")),
    "arguments": _integer(limits.get("arguments")),
    "command_timeout_seconds": _integer(limits.get("command_timeout_seconds")),
    "binary": _text(values.get("binary")),
    "install_flag": _text(values.get("install_flag")),
    "localization_key": _text(values.get("localization_key")),
    "config_content": _text(values.get("config_content")),
    "read_default": _strings(commands.get("read_default")),
    "command_missing": _strings(commands.get("command_missing")),
    "launch_installer": _strings(commands.get("launch_installer")),
    "notification": _strings(commands.get("notification")),
    "localization": _strings(commands.get("localization")),
    "apps": apps,
    "usage": _text(messages.get("usage")),
    "command_error": _text(messages.get("command_error")),
    "success": _integer(statuses.get("success")),
    "invalid_arguments": _integer(statuses.get("invalid_arguments")),
    "invalid_selection": _integer(statuses.get("invalid_selection")),
    "command_error_status": _integer(statuses.get("command_error")),
  }


def _config_path(settings: Settings) -> Path:
  config_home = os.environ.get(settings["config_home_environment"])
  if config_home is None or config_home == "":
    relative = Path(settings["default_config_home"])
    if relative.is_absolute() or ".." in relative.parts:
      raise ValueError()
    root = Path(os.environ[settings["home_environment"]]).joinpath(*relative.parts)
  else:
    root = Path(config_home)
  relative_config = Path(settings["config_relative"])
  if relative_config.is_absolute() or ".." in relative_config.parts:
    raise ValueError()
  return root.joinpath(*relative_config.parts)


def _run(command: list[str], settings: Settings, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    command,
    check=False,
    capture_output=capture,
    text=True,
    timeout=settings["command_timeout_seconds"] if capture else None,
  )


def _selected(arguments: list[str], settings: Settings) -> tuple[bool, str | None]:
  installing = bool(arguments and arguments[0] == settings["install_flag"])
  remaining = arguments[1:] if installing else arguments
  if len(remaining) > settings["arguments"]:
    return installing, None
  return installing, remaining[0] if remaining else None


def _print_current(settings: Settings) -> int:
  try:
    result = _run(settings["read_default"], settings, capture=True)
    desktop_id = result.stdout.split(":", maxsplit=1)[0]
  except (OSError, subprocess.SubprocessError, UnicodeError):
    desktop_id = ""
  for name, app in settings["apps"].items():
    if app["desktop_id"] == desktop_id:
      print(name)
      return settings["success"]
  print(desktop_id)
  return settings["success"]


def default_terminal_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, UnicodeError, ValueError, yaml.YAMLError):
    print("Could not load terminal command settings.", file=sys.stderr)
    return 1

  installing, selection = _selected(arguments, settings)
  if selection is None and (not arguments or installing and len(arguments) == 1):
    return _print_current(settings)
  if selection is None:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]

  app = settings["apps"].get(selection)
  if app is None:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_selection"]

  try:
    missing = _run([*settings["command_missing"], app["command"]], settings)
    if missing.returncode == settings["success"]:
      if not installing:
        return _run([*settings["launch_installer"], settings["binary"], settings["install_flag"], selection], settings).returncode
      installed = _run(app["installer"], settings)
      if installed.returncode != settings["success"]:
        return installed.returncode

    config_path = _config_path(settings)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
      settings["config_content"].format(desktop_id=app["desktop_id"]),
      encoding=settings["encoding"],
    )
    localized = _run([*settings["localization"], settings["localization_key"], app["name"]], settings, capture=True)
    return _run([*settings["notification"], app["glyph"], localized.stdout.rstrip("\n")], settings).returncode
  except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
    print(settings["command_error"], file=sys.stderr)
    return settings["command_error_status"]
