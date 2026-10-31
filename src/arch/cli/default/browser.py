from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Browser(TypedDict):
  command: str
  desktop_id: str
  name: str
  glyph: str
  installer: str


class Settings(TypedDict):
  arguments: int
  command_timeout_seconds: int
  install_flag: str
  localization_key: str
  default_route: list[str]
  read_default: list[str]
  command_missing: list[str]
  launch_installer: list[str]
  install_browser: list[str]
  set_default: list[str]
  localization: list[str]
  notification: list[str]
  browser_environment: str
  desktop_environment: str
  desktop_environment_value: str
  apps: dict[str, Browser]
  usage: str
  command_error: str
  success: int
  invalid_arguments: int
  invalid_selection: int
  set_default_failed: int
  command_error_status: int


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError()
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError()
  return value


def _text_or_empty(value: object) -> str:
  if not isinstance(value, str):
    raise TypeError()
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
  config_path = Path(os.environ["AP"]) / "data/cli/default-browser.yml"
  with config_path.open(encoding="utf-8") as stream:
    document = _mapping(yaml.safe_load(stream))
  limits = _mapping(document.get("limits"))
  values = _mapping(document.get("values"))
  commands = _mapping(document.get("commands"))
  environment = _mapping(document.get("environment"))
  raw_apps = _mapping(document.get("browsers"))
  apps: dict[str, Browser] = {}
  for selection, raw_app in raw_apps.items():
    app = _mapping(raw_app)
    apps[selection] = {
      "command": _text(app.get("command")),
      "desktop_id": _text(app.get("desktop_id")),
      "name": _text(app.get("name")),
      "glyph": _text(app.get("glyph")),
      "installer": _text(app.get("installer")),
    }
  messages = _mapping(document.get("messages"))
  statuses = _mapping(document.get("statuses"))
  return {
    "arguments": _integer(limits.get("arguments")),
    "command_timeout_seconds": _integer(limits.get("command_timeout_seconds")),
    "install_flag": _text(values.get("install_flag")),
    "localization_key": _text(values.get("localization_key")),
    "default_route": _strings(values.get("default_route")),
    "read_default": _strings(commands.get("read_default")),
    "command_missing": _strings(commands.get("command_missing")),
    "launch_installer": _strings(commands.get("launch_installer")),
    "install_browser": _strings(commands.get("install_browser")),
    "set_default": _strings(commands.get("set_default")),
    "localization": _strings(commands.get("localization")),
    "notification": _strings(commands.get("notification")),
    "browser_environment": _text(environment.get("browser")),
    "desktop_environment": _text(environment.get("desktop")),
    "desktop_environment_value": _text_or_empty(environment.get("desktop_value")),
    "apps": apps,
    "usage": _text(messages.get("usage")),
    "command_error": _text(messages.get("command_error")),
    "success": _integer(statuses.get("success")),
    "invalid_arguments": _integer(statuses.get("invalid_arguments")),
    "invalid_selection": _integer(statuses.get("invalid_selection")),
    "set_default_failed": _integer(statuses.get("set_default_failed")),
    "command_error_status": _integer(statuses.get("command_error")),
  }


def _run(
  command: list[str],
  *,
  capture: bool = False,
  timeout: int | None = None,
  environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    command,
    check=False,
    capture_output=capture,
    text=True,
    timeout=timeout,
    env=environment,
  )


def _print_current(settings: Settings) -> int:
  try:
    result = _run(
      settings["read_default"],
      capture=True,
      timeout=settings["command_timeout_seconds"],
    )
    desktop_id = result.stdout.splitlines()[0] if result.stdout.splitlines() else ""
  except (OSError, subprocess.SubprocessError, UnicodeError):
    desktop_id = ""
  for name, app in settings["apps"].items():
    if app["desktop_id"] == desktop_id:
      print(name)
      return settings["success"]
  print(desktop_id)
  return settings["success"]


def default_browser_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return 1

  installing = bool(arguments and arguments[0] == settings["install_flag"])
  selections = arguments[1:] if installing else arguments
  if len(selections) > settings["arguments"]:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]
  if not selections:
    return _print_current(settings)

  selection = selections[0]
  browser = settings["apps"].get(selection)
  if browser is None:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_selection"]

  try:
    missing = _run(
      [*settings["command_missing"], browser["command"]],
      timeout=settings["command_timeout_seconds"],
    )
    if missing.returncode == settings["success"]:
      if not installing:
        return _run(
          [*settings["launch_installer"], *settings["default_route"], settings["install_flag"], selection],
        ).returncode
      installed = _run([*settings["install_browser"], browser["installer"]])
      if installed.returncode != settings["success"]:
        return installed.returncode

    environment = os.environ.copy()
    environment.pop(settings["browser_environment"], None)
    environment[settings["desktop_environment"]] = settings["desktop_environment_value"]
    updated = _run(
      [*settings["set_default"], browser["desktop_id"]],
      timeout=settings["command_timeout_seconds"],
      environment=environment,
    )
    if updated.returncode != settings["success"]:
      return settings["set_default_failed"]

    localized = _run(
      [*settings["localization"], settings["localization_key"], browser["name"]],
      capture=True,
      timeout=settings["command_timeout_seconds"],
    )
    return _run(
      [*settings["notification"], browser["glyph"], localized.stdout.rstrip("\n")],
      timeout=settings["command_timeout_seconds"],
    ).returncode
  except (OSError, subprocess.SubprocessError, UnicodeError):
    print(settings["command_error"], file=sys.stderr)
    return settings["command_error_status"]
