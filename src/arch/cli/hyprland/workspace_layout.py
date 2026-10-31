from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
from typing import TypedDict, cast

import yaml


class Paths(TypedDict):
  home_environment: str
  state_home_environment: str
  default_state_home_relative: str
  layout_directory: str
  default_file_name: str
  workspace_file_suffix: str


class Commands(TypedDict):
  active_workspace: list[str]
  workspaces: list[str]
  default_layout: list[str]


class Fields(TypedDict):
  workspace_id: str
  tiled_layout: str


class Values(TypedDict):
  tiling_modes: list[str]
  scrolling_modes: list[str]
  fallback_mode: str


class Patterns(TypedDict):
  workspace_id: str
  saved_mode: str


class Limits(TypedDict):
  command_timeout_seconds: int
  saved_file_characters: int
  workspace_id_digits: int


class Statuses(TypedDict):
  success: int
  configuration_error: int


class Settings(TypedDict):
  paths: Paths
  commands: Commands
  fields: Fields
  values: Values
  patterns: Patterns
  limits: Limits
  statuses: Statuses


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError()
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError()
  return value


def _strings(value: object) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError()
  return cast(list[str], value)


def _command(value: object) -> list[str]:
  return _strings(value)


def _positive_integer(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
    raise ValueError()
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw = yaml.safe_load((root / "data/cli/hyprland-workspace-layout-current.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  paths = _mapping(document.get("paths"))
  commands = _mapping(document.get("commands"))
  fields = _mapping(document.get("fields"))
  values = _mapping(document.get("values"))
  patterns = _mapping(document.get("patterns"))
  limits = _mapping(document.get("limits"))
  statuses = _mapping(document.get("statuses"))
  success = statuses.get("success")
  if not isinstance(success, int) or isinstance(success, bool) or success < 0:
    raise ValueError()
  return {
    "paths": {
      "home_environment": _text(paths.get("home_environment")),
      "state_home_environment": _text(paths.get("state_home_environment")),
      "default_state_home_relative": _text(paths.get("default_state_home_relative")),
      "layout_directory": _text(paths.get("layout_directory")),
      "default_file_name": _text(paths.get("default_file_name")),
      "workspace_file_suffix": _text(paths.get("workspace_file_suffix")),
    },
    "commands": {
      "active_workspace": _command(commands.get("active_workspace")),
      "workspaces": _command(commands.get("workspaces")),
      "default_layout": _command(commands.get("default_layout")),
    },
    "fields": {
      "workspace_id": _text(fields.get("workspace_id")),
      "tiled_layout": _text(fields.get("tiled_layout")),
    },
    "values": {
      "tiling_modes": _strings(values.get("tiling_modes")),
      "scrolling_modes": _strings(values.get("scrolling_modes")),
      "fallback_mode": _text(values.get("fallback_mode")),
    },
    "patterns": {
      "workspace_id": _text(patterns.get("workspace_id")),
      "saved_mode": _text(patterns.get("saved_mode")),
    },
    "limits": {
      "command_timeout_seconds": _positive_integer(limits.get("command_timeout_seconds")),
      "saved_file_characters": _positive_integer(limits.get("saved_file_characters")),
      "workspace_id_digits": _positive_integer(limits.get("workspace_id_digits")),
    },
    "statuses": {
      "success": success,
      "configuration_error": _positive_integer(statuses.get("configuration_error")),
    },
  }


def _run_json(command: list[str], settings: Settings) -> object | None:
  try:
    result = subprocess.run(
      command,
      check=False,
      capture_output=True,
      text=True,
      timeout=settings["limits"]["command_timeout_seconds"],
    )
    return json.loads(result.stdout)
  except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
    return None


def _workspace_data(arguments: list[str], settings: Settings) -> tuple[str, str]:
  fields = settings["fields"]
  if arguments:
    workspace_id = arguments[0]
    workspaces = _run_json(settings["commands"]["workspaces"], settings)
    if isinstance(workspaces, list):
      for workspace in workspaces:
        if not isinstance(workspace, dict):
          continue
        candidate_id = workspace.get(fields["workspace_id"])
        if isinstance(candidate_id, (str, int)) and not isinstance(candidate_id, bool) and str(candidate_id) == workspace_id:
          layout = workspace.get(fields["tiled_layout"])
          return workspace_id, layout if isinstance(layout, str) else ""
    return workspace_id, ""

  active = _run_json(settings["commands"]["active_workspace"], settings)
  if not isinstance(active, dict):
    return "", ""
  workspace_id = active.get(fields["workspace_id"])
  layout = active.get(fields["tiled_layout"])
  return str(workspace_id) if isinstance(workspace_id, (str, int)) and not isinstance(workspace_id, bool) else "", layout if isinstance(layout, str) else ""


def _state_directory(settings: Settings) -> Path:
  paths = settings["paths"]
  state_home = os.environ.get(paths["state_home_environment"], "")
  if state_home:
    root = Path(state_home)
  else:
    relative = Path(paths["default_state_home_relative"])
    if relative.is_absolute() or ".." in relative.parts:
      raise ValueError()
    root = Path(os.environ[paths["home_environment"]]).joinpath(*relative.parts)
  relative_layout = Path(paths["layout_directory"])
  if relative_layout.is_absolute() or ".." in relative_layout.parts:
    raise ValueError()
  return root.joinpath(*relative_layout.parts)


def _saved_mode(path: Path, settings: Settings) -> str:
  try:
    with path.open(encoding="utf-8") as stream:
      contents = stream.read(settings["limits"]["saved_file_characters"] + 1)
  except (OSError, UnicodeError):
    return ""
  if len(contents) > settings["limits"]["saved_file_characters"]:
    return ""
  match = re.search(settings["patterns"]["saved_mode"], contents, re.MULTILINE)
  if match:
    mode = match.group(1)
    if isinstance(mode, str):
      return mode
  return ""


def _default_mode(settings: Settings) -> str:
  try:
    result = subprocess.run(
      settings["commands"]["default_layout"],
      check=False,
      capture_output=True,
      text=True,
      timeout=settings["limits"]["command_timeout_seconds"],
    )
    return result.stdout.rstrip("\n")
  except (OSError, subprocess.SubprocessError, UnicodeError):
    return ""


def _normalize(mode: str, settings: Settings) -> str:
  values = settings["values"]
  if mode in values["tiling_modes"]:
    return values["tiling_modes"][0]
  if mode in values["scrolling_modes"]:
    return values["scrolling_modes"][0]
  return values["fallback_mode"]


def workspace_layout_current_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
    workspace_id, tiled_layout = _workspace_data(arguments, settings)
    mode = ""
    if (
      re.fullmatch(settings["patterns"]["workspace_id"], workspace_id)
      and len(workspace_id) <= settings["limits"]["workspace_id_digits"]
      and int(workspace_id) >= 1
    ):
      layout_directory = _state_directory(settings)
      mode = _saved_mode(
        layout_directory / f"{workspace_id}{settings['paths']['workspace_file_suffix']}",
        settings,
      )
      default_file = layout_directory / settings["paths"]["default_file_name"]
      if not mode and default_file.is_file():
        mode = _default_mode(settings)
    print(_normalize(mode or tiled_layout, settings))
    return settings["statuses"]["success"]
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError, re.error):
    return os.EX_CONFIG
