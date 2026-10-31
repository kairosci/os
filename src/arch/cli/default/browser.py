from __future__ import annotations

import os
import shutil
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


class CurrentBrowser(TypedDict):
  applications_directory: str
  mimeapps_filename: str
  desktop_mimeapps_suffix: str
  application_exec_prefix: str
  default_applications_section: str
  http_handler_key: str
  browser_link_entry: str
  entry_separator: str
  path_separator: str
  max_mimeapps_bytes: int
  max_desktop_entry_bytes: int


class Settings(TypedDict):
  arguments: int
  command_timeout_seconds: int
  install_flag: str
  localization_key: str
  default_route: list[str]
  current_fallbacks: list[list[str]]
  command_missing: list[str]
  launch_installer: list[str]
  install_browser: list[str]
  set_default: list[str]
  localization: list[str]
  notification: list[str]
  browser_environment: str
  desktop_environment: str
  desktop_environment_value: str
  data_home_environment: str
  data_dirs_environment: str
  config_home_environment: str
  config_dirs_environment: str
  data_home_suffix: str
  data_dirs: list[str]
  config_home_suffix: str
  config_dirs: list[str]
  current_browser: CurrentBrowser
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
  defaults = _mapping(document.get("defaults"))
  raw_current_browser = _mapping(document.get("current_browser"))
  raw_fallbacks = commands.get("current_fallbacks")
  if not isinstance(raw_fallbacks, list) or not all(
    isinstance(command, list) and command and all(isinstance(token, str) and token for token in command)
    for command in raw_fallbacks
  ):
    raise ValueError()
  current_browser: CurrentBrowser = {
    "applications_directory": _text(raw_current_browser.get("applications_directory")),
    "mimeapps_filename": _text(raw_current_browser.get("mimeapps_filename")),
    "desktop_mimeapps_suffix": _text(raw_current_browser.get("desktop_mimeapps_suffix")),
    "application_exec_prefix": _text(raw_current_browser.get("application_exec_prefix")),
    "default_applications_section": _text(raw_current_browser.get("default_applications_section")),
    "http_handler_key": _text(raw_current_browser.get("http_handler_key")),
    "browser_link_entry": _text(raw_current_browser.get("browser_link_entry")),
    "entry_separator": _text(raw_current_browser.get("entry_separator")),
    "path_separator": _text(raw_current_browser.get("path_separator")),
    "max_mimeapps_bytes": _integer(raw_current_browser.get("max_mimeapps_bytes")),
    "max_desktop_entry_bytes": _integer(raw_current_browser.get("max_desktop_entry_bytes")),
  }
  return {
    "arguments": _integer(limits.get("arguments")),
    "command_timeout_seconds": _integer(limits.get("command_timeout_seconds")),
    "install_flag": _text(values.get("install_flag")),
    "localization_key": _text(values.get("localization_key")),
    "default_route": _strings(values.get("default_route")),
    "current_fallbacks": cast(list[list[str]], raw_fallbacks),
    "command_missing": _strings(commands.get("command_missing")),
    "launch_installer": _strings(commands.get("launch_installer")),
    "install_browser": _strings(commands.get("install_browser")),
    "set_default": _strings(commands.get("set_default")),
    "localization": _strings(commands.get("localization")),
    "notification": _strings(commands.get("notification")),
    "browser_environment": _text(environment.get("browser")),
    "desktop_environment": _text(environment.get("desktop")),
    "desktop_environment_value": _text_or_empty(environment.get("desktop_value")),
    "data_home_environment": _text(environment.get("data_home")),
    "data_dirs_environment": _text(environment.get("data_dirs")),
    "config_home_environment": _text(environment.get("config_home")),
    "config_dirs_environment": _text(environment.get("config_dirs")),
    "data_home_suffix": _text(defaults.get("data_home_suffix")),
    "data_dirs": _strings(defaults.get("data_dirs")),
    "config_home_suffix": _text(defaults.get("config_home_suffix")),
    "config_dirs": _strings(defaults.get("config_dirs")),
    "current_browser": current_browser,
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
    desktop_id = _current_desktop_id(settings)
  except (OSError, subprocess.SubprocessError, UnicodeError):
    desktop_id = ""
  for name, app in settings["apps"].items():
    if app["desktop_id"] == desktop_id:
      print(name)
      return settings["success"]
  print(desktop_id)
  return settings["success"]


def _xdg_directories(
  environment: str,
  default_suffix: str,
  fallback: list[str],
  path_separator: str,
) -> list[Path]:
  configured = os.environ.get(environment)
  if configured:
    return [Path(item) for item in configured.split(path_separator) if item]
  if default_suffix:
    return [Path.home() / default_suffix]
  return [Path(item) for item in fallback]


def _current_desktop_id(settings: Settings) -> str:
  config = settings["current_browser"]
  data_directories = _xdg_directories(
    settings["data_dirs_environment"], "", settings["data_dirs"], config["path_separator"]
  )
  data_home = _xdg_directories(
    settings["data_home_environment"], settings["data_home_suffix"], [], config["path_separator"]
  )
  config_directories = _xdg_directories(
    settings["config_dirs_environment"], "", settings["config_dirs"], config["path_separator"]
  )
  config_home = _xdg_directories(
    settings["config_home_environment"], settings["config_home_suffix"], [], config["path_separator"]
  )
  data_directories = [*data_home, *data_directories]
  config_directories = [*config_home, *config_directories]
  desktop_environment = os.environ.get(settings["desktop_environment"], "")
  desktops = [*desktop_environment.split(":"), ""]
  mimeapps_filename = config["mimeapps_filename"]
  desktop_suffix = config["desktop_mimeapps_suffix"]
  section = config["default_applications_section"]
  handler = config["http_handler_key"]
  app_dir = config["applications_directory"]
  exec_prefix = config["application_exec_prefix"]
  separator = config["entry_separator"]
  browser_link = config["browser_link_entry"]
  mimeapps_limit = config["max_mimeapps_bytes"]
  desktop_limit = config["max_desktop_entry_bytes"]

  for config_directory in config_directories:
    for desktop in desktops:
      filename = f"{desktop.lower()}{desktop_suffix}" if desktop else mimeapps_filename
      path = config_directory / filename
      try:
        with path.open(encoding="utf-8") as stream:
          contents = stream.read(mimeapps_limit + 1)
      except (OSError, UnicodeError):
        continue
      if len(contents.encode("utf-8")) > mimeapps_limit:
        continue
      in_defaults = False
      entries = ""
      for line in contents.splitlines():
        if line.startswith("["):
          in_defaults = line == section
          continue
        if in_defaults and line.startswith(handler):
          entries = line[len(handler):]
          break
      for entry in entries.split(separator):
        if not entry or entry == browser_link:
          continue
        for data_directory in data_directories:
          desktop_file = data_directory / app_dir / entry
          try:
            with desktop_file.open(encoding="utf-8") as stream:
              app_contents = stream.read(desktop_limit + 1)
          except (OSError, UnicodeError):
            continue
          if len(app_contents.encode("utf-8")) > desktop_limit:
            break
          command = next(
            (
              line[len(exec_prefix):].split(" ", 1)[0]
              for line in app_contents.splitlines()
              if line.startswith(exec_prefix)
            ),
            "",
          )
          if command and shutil.which(command):
            return entry
          break

  environment = os.environ.copy()
  environment.pop(settings["browser_environment"], None)
  environment[settings["desktop_environment"]] = settings["desktop_environment_value"]
  for index, command in enumerate(settings["current_fallbacks"]):
    try:
      result = _run(
        command,
        capture=True,
        timeout=settings["command_timeout_seconds"],
        environment=environment if index == 0 else None,
      )
    except OSError:
      continue
    value = result.stdout.splitlines()[0] if result.stdout.splitlines() else ""
    if value and value != browser_link:
      return value
  return ""


def default_browser_desktop_id_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
    if arguments:
      return settings["invalid_arguments"]
    desktop_id = _current_desktop_id(settings)
    if not desktop_id:
      return settings["invalid_selection"]
    print(desktop_id)
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, subprocess.SubprocessError, yaml.YAMLError):
    return 1
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
