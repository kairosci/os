from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Literal, TypedDict, cast

import yaml


class Paths(TypedDict):
  home_environment: str
  state_home_environment: str
  default_state_home_relative: str
  layout_directory: str
  default_file_name: str
  workspace_file_suffix: str
  notification_file_name: str
  state_namespace: str
  temporary_prefix: str


class Commands(TypedDict):
  active_workspace: list[str]
  workspaces: list[str]
  default_layout: list[str]
  apply_workspace_layout: list[str]
  reload: list[str]
  refresh_workspaces: list[str]
  notification_send: list[str]
  notification_flags: list[str]
  localize: list[str]


class Fields(TypedDict):
  workspace_id: str
  tiled_layout: str
  window_count: str
  default_layout: str


class Values(TypedDict):
  tiling_modes: list[str]
  scrolling_modes: list[str]
  fallback_mode: str
  public_modes: list[str]
  toggle_back_argument: str
  empty_notification_id: str
  notification_glyph: str
  workspace_layout_expression: str
  default_layout_expression: str
  workspace_layout_notification: str
  workspace_layout_unsaved_notification: str
  scrolling_layout_notification: str
  scrolling_layout_unsaved_notification: str
  default_tiling_notification: str
  default_scrolling_notification: str
  reload_required_notification: str


class Patterns(TypedDict):
  workspace_id: str
  notification_id: str
  saved_mode: str
  saved_default_mode: str


class Limits(TypedDict):
  command_timeout_seconds: int
  saved_file_characters: int
  workspace_id_digits: int
  notification_id_characters: int


class Statuses(TypedDict):
  success: int
  configuration_error: int
  invalid_arguments: int
  command_failure: int


class Settings(TypedDict):
  paths: Paths
  commands: Commands
  fields: Fields
  values: Values
  patterns: Patterns
  limits: Limits
  statuses: Statuses
  messages: dict[str, str]


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
  raw = yaml.safe_load((root / "data/cli/hyprland-workspace-layout.yml").read_text(encoding="utf-8"))
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
      "notification_file_name": _text(paths.get("notification_file_name")),
      "state_namespace": _text(paths.get("state_namespace")),
      "temporary_prefix": _text(paths.get("temporary_prefix")),
    },
    "commands": {
      "active_workspace": _command(commands.get("active_workspace")),
      "workspaces": _command(commands.get("workspaces")),
      "default_layout": _command(commands.get("default_layout")),
      "apply_workspace_layout": _command(commands.get("apply_workspace_layout")),
      "reload": _command(commands.get("reload")),
      "refresh_workspaces": _command(commands.get("refresh_workspaces")),
      "notification_send": _command(commands.get("notification_send")),
      "notification_flags": _command(commands.get("notification_flags")),
      "localize": _command(commands.get("localize")),
    },
    "fields": {
      "workspace_id": _text(fields.get("workspace_id")),
      "tiled_layout": _text(fields.get("tiled_layout")),
      "window_count": _text(fields.get("window_count")),
      "default_layout": _text(fields.get("default_layout")),
    },
    "values": {
      "tiling_modes": _strings(values.get("tiling_modes")),
      "scrolling_modes": _strings(values.get("scrolling_modes")),
      "fallback_mode": _text(values.get("fallback_mode")),
      "public_modes": _strings(values.get("public_modes")),
      "toggle_back_argument": _text(values.get("toggle_back_argument")),
      "empty_notification_id": _text(values.get("empty_notification_id")),
      "notification_glyph": _text(values.get("notification_glyph")),
      "workspace_layout_expression": _text(values.get("workspace_layout_expression")),
      "default_layout_expression": _text(values.get("default_layout_expression")),
      "workspace_layout_notification": _text(values.get("workspace_layout_notification")),
      "workspace_layout_unsaved_notification": _text(values.get("workspace_layout_unsaved_notification")),
      "scrolling_layout_notification": _text(values.get("scrolling_layout_notification")),
      "scrolling_layout_unsaved_notification": _text(values.get("scrolling_layout_unsaved_notification")),
      "default_tiling_notification": _text(values.get("default_tiling_notification")),
      "default_scrolling_notification": _text(values.get("default_scrolling_notification")),
      "reload_required_notification": _text(values.get("reload_required_notification")),
    },
    "patterns": {
      "workspace_id": _text(patterns.get("workspace_id")),
      "notification_id": _text(patterns.get("notification_id")),
      "saved_mode": _text(patterns.get("saved_mode")),
      "saved_default_mode": _text(patterns.get("saved_default_mode")),
    },
    "limits": {
      "command_timeout_seconds": _positive_integer(limits.get("command_timeout_seconds")),
      "saved_file_characters": _positive_integer(limits.get("saved_file_characters")),
      "workspace_id_digits": _positive_integer(limits.get("workspace_id_digits")),
      "notification_id_characters": _positive_integer(limits.get("notification_id_characters")),
    },
    "statuses": {
      "success": success,
      "configuration_error": _positive_integer(statuses.get("configuration_error")),
      "invalid_arguments": _positive_integer(statuses.get("invalid_arguments")),
      "command_failure": _positive_integer(statuses.get("command_failure")),
    },
    "messages": {key: _text(value) for key, value in _mapping(document.get("messages")).items()},
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
    if result.returncode != settings["statuses"]["success"]:
      return None
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
  contents = _read_state_file(path, settings)
  match = re.search(settings["patterns"]["saved_mode"], contents, re.MULTILINE)
  if match:
    mode = match.group(1)
    if isinstance(mode, str):
      return mode
  return ""


def _default_mode(settings: Settings) -> str:
  try:
    default_match = re.search(
      settings["patterns"]["saved_default_mode"],
      _read_state_file(
        _state_directory(settings) / settings["paths"]["default_file_name"],
        settings,
      ),
      re.MULTILINE,
    )
    saved_default = default_match.group(1) if default_match else ""
    if saved_default:
      return _normalize(saved_default, settings)
  except (OSError, TypeError, ValueError, re.error):
    pass
  try:
    result = subprocess.run(
      settings["commands"]["default_layout"],
      check=False,
      capture_output=True,
      text=True,
      timeout=settings["limits"]["command_timeout_seconds"],
    )
    if result.returncode != settings["statuses"]["success"]:
      return ""
    decoded = json.loads(result.stdout)
    if not isinstance(decoded, dict):
      return ""
    layout = decoded.get(settings["fields"]["default_layout"])
    return layout if isinstance(layout, str) else ""
  except (OSError, subprocess.SubprocessError, UnicodeError):
    return ""
  except (TypeError, ValueError):
    return ""


def _normalize(mode: str, settings: Settings) -> str:
  values = settings["values"]
  if mode in values["tiling_modes"]:
    return values["tiling_modes"][0]
  if mode in values["scrolling_modes"]:
    return values["scrolling_modes"][0]
  return values["fallback_mode"]


def _read_state_file(path: Path, settings: Settings) -> str:
  try:
    descriptor = os.open(
      path,
      os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
    )
  except OSError:
    return ""
  try:
    with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
      contents = stream.read(settings["limits"]["saved_file_characters"] + 1)
  except (OSError, UnicodeError):
    return ""
  if len(contents) > settings["limits"]["saved_file_characters"]:
    return ""
  return contents


def _write_state_file(path: Path, contents: str, settings: Settings) -> None:
  path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
  temporary_path: Path | None = None
  try:
    with tempfile.NamedTemporaryFile(
      mode="w",
      encoding="utf-8",
      dir=path.parent,
      prefix=settings["paths"]["temporary_prefix"],
      delete=False,
    ) as temporary:
      temporary_path = Path(temporary.name)
      temporary.write(contents)
      temporary.flush()
      os.fsync(temporary.fileno())
    os.replace(temporary_path, path)
    temporary_path = None
  finally:
    if temporary_path is not None:
      temporary_path.unlink(missing_ok=True)


def _localized_message(key: str, settings: Settings) -> str:
  try:
    result = subprocess.run(
      [*settings["commands"]["localize"], key],
      check=False,
      capture_output=True,
      text=True,
      timeout=settings["limits"]["command_timeout_seconds"],
    )
  except (OSError, subprocess.SubprocessError, UnicodeError):
    return ""
  return result.stdout.rstrip("\n") if result.returncode == settings["statuses"]["success"] else ""


def _notify(message_key: str, fallback_key: str, settings: Settings) -> None:
  message = _localized_message(message_key, settings)
  if not message:
    message = settings["messages"].get(fallback_key, "")
  if not message:
    return
  paths = settings["paths"]
  state_home = os.environ.get(paths["state_home_environment"], "")
  if state_home:
    notification_state = Path(state_home) / paths["state_namespace"] / paths["notification_file_name"]
  else:
    notification_state = Path(os.environ[paths["home_environment"]]) / paths["default_state_home_relative"] / paths["state_namespace"] / paths["notification_file_name"]
  last_id = _read_state_file(notification_state, settings).strip()
  if not re.fullmatch(settings["patterns"]["notification_id"], last_id) or len(last_id) > settings["limits"]["notification_id_characters"]:
    last_id = settings["values"]["empty_notification_id"]
  try:
    result = subprocess.run(
      [
        *settings["commands"]["notification_send"],
        settings["commands"]["notification_flags"][0],
        settings["commands"]["notification_flags"][1],
        last_id,
        settings["commands"]["notification_flags"][2],
        settings["values"]["notification_glyph"],
        message,
      ],
      check=False,
      capture_output=True,
      text=True,
      timeout=settings["limits"]["command_timeout_seconds"],
    )
  except (OSError, subprocess.SubprocessError, UnicodeError):
    return
  result_id = result.stdout.strip()
  if (
    result.returncode == settings["statuses"]["success"]
    and re.fullmatch(settings["patterns"]["notification_id"], result_id)
    and len(result_id) <= settings["limits"]["notification_id_characters"]
  ):
    try:
      _write_state_file(notification_state, result_id + "\n", settings)
    except OSError:
      pass


def _report(
  message_key: str,
  status_key: Literal["invalid_arguments", "command_failure", "configuration_error"],
  settings: Settings,
) -> int:
  print(settings["messages"][message_key], file=sys.stderr)
  return settings["statuses"][status_key]


def _workspace_id(value: object, settings: Settings) -> str:
  if isinstance(value, bool) or not isinstance(value, (str, int)):
    return ""
  workspace_id = str(value)
  if (
    len(workspace_id) > settings["limits"]["workspace_id_digits"]
    or not re.fullmatch(settings["patterns"]["workspace_id"], workspace_id)
    or int(workspace_id) < 1
  ):
    return ""
  return workspace_id


def _workspace_layout_expression(workspace_id: str, mode: str, settings: Settings) -> str:
  return settings["values"]["workspace_layout_expression"].format(
    workspace=workspace_id,
    mode=mode,
  ) + "\n"


def _current_layout(workspace_id: str, tiled_layout: str, settings: Settings) -> str:
  mode = ""
  if _workspace_id(workspace_id, settings):
    layout_directory = _state_directory(settings)
    mode = _saved_mode(
      layout_directory / f"{workspace_id}{settings['paths']['workspace_file_suffix']}",
      settings,
    )
    if not mode and (layout_directory / settings["paths"]["default_file_name"]).is_file():
      mode = _default_mode(settings)
  return _normalize(mode or tiled_layout, settings)


def _refresh_workspaces(settings: Settings) -> None:
  try:
    subprocess.run(
      settings["commands"]["refresh_workspaces"],
      check=False,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      timeout=settings["limits"]["command_timeout_seconds"],
    )
  except (OSError, subprocess.SubprocessError):
    pass


def workspace_layout_current_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
    if len(arguments) > 1 or (arguments and not _workspace_id(arguments[0], settings)):
      return _report("current_usage", "invalid_arguments", settings)
    workspace_id, tiled_layout = _workspace_data(arguments, settings)
    print(_current_layout(workspace_id, tiled_layout, settings))
    return settings["statuses"]["success"]
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError, re.error):
    return os.EX_CONFIG


def _busy_workspaces(settings: Settings) -> tuple[set[str], list[dict[str, object]]] | None:
  entries = _run_json(settings["commands"]["workspaces"], settings)
  if not isinstance(entries, list):
    return None
  busy_ids: set[str] = set()
  valid_entries: list[dict[str, object]] = []
  fields = settings["fields"]
  for entry in entries:
    if not isinstance(entry, dict):
      continue
    workspace_id = _workspace_id(entry.get(fields["workspace_id"]), settings)
    windows = entry.get(fields["window_count"])
    if not workspace_id or isinstance(windows, bool) or not isinstance(windows, int):
      continue
    valid_entries.append(entry)
    if windows > 0:
      busy_ids.add(workspace_id)
  return busy_ids, valid_entries


def workspace_layout_default_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
    if len(arguments) > 1:
      return _report("default_usage", "invalid_arguments", settings)
    if not arguments:
      print(_normalize(_default_mode(settings), settings))
      return settings["statuses"]["success"]

    requested = arguments[0]
    values = settings["values"]
    if requested not in values["public_modes"]:
      return _report("default_usage", "invalid_arguments", settings)
    mode = _normalize(requested, settings)
    workspaces = _busy_workspaces(settings)
    if workspaces is None:
      return _report("workspaces_query_failed", "command_failure", settings)
    busy_ids, entries = workspaces
    layout_directory = _state_directory(settings)
    fields = settings["fields"]
    for entry in entries:
      workspace_id = _workspace_id(entry.get(fields["workspace_id"]), settings)
      windows = entry.get(fields["window_count"])
      if not workspace_id or workspace_id not in busy_ids or not isinstance(windows, int) or isinstance(windows, bool):
        continue
      workspace_file = layout_directory / f"{workspace_id}{settings['paths']['workspace_file_suffix']}"
      if workspace_file.exists() or workspace_file.is_symlink():
        continue
      tiled_layout = entry.get(fields["tiled_layout"])
      current = _current_layout(
        workspace_id,
        tiled_layout if isinstance(tiled_layout, str) else "",
        settings,
      )
      if current != mode:
        expression = _workspace_layout_expression(workspace_id, current, settings)
        _write_state_file(workspace_file, expression, settings)

    for workspace_file in layout_directory.glob(f"[0-9]*{settings['paths']['workspace_file_suffix']}"):
      workspace_id = workspace_file.name.removesuffix(settings["paths"]["workspace_file_suffix"])
      if _workspace_id(workspace_id, settings) and workspace_id not in busy_ids:
        workspace_file.unlink(missing_ok=True)

    default_file = layout_directory / settings["paths"]["default_file_name"]
    expression = values["default_layout_expression"].format(mode=mode) + "\n"
    _write_state_file(default_file, expression, settings)
    try:
      result = subprocess.run(
        settings["commands"]["reload"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=settings["limits"]["command_timeout_seconds"],
      )
    except (OSError, subprocess.SubprocessError):
      _notify(values["reload_required_notification"], "reload_failed", settings)
      return settings["statuses"]["command_failure"]
    if result.returncode != settings["statuses"]["success"]:
      _notify(values["reload_required_notification"], "reload_failed", settings)
      return settings["statuses"]["command_failure"]

    _refresh_workspaces(settings)
    message_key = values["default_tiling_notification"] if mode == values["tiling_modes"][0] else values["default_scrolling_notification"]
    _notify(message_key, "default_set", settings)
    return settings["statuses"]["success"]
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError, re.error, subprocess.SubprocessError):
    try:
      return _report("configuration_failed", "configuration_error", _settings())
    except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
      return os.EX_CONFIG


def workspace_layout_toggle_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
    values = settings["values"]
    if len(arguments) > 1 or (arguments and arguments[0] != values["toggle_back_argument"]):
      return _report("toggle_usage", "invalid_arguments", settings)

    workspace_id, tiled_layout = _workspace_data([], settings)
    if not _workspace_id(workspace_id, settings):
      return _report("workspace_query_failed", "command_failure", settings)
    current = _current_layout(workspace_id, tiled_layout, settings)
    new_mode = values["scrolling_modes"][0] if current in values["tiling_modes"] else values["tiling_modes"][0]
    expression = _workspace_layout_expression(workspace_id, new_mode, settings).rstrip("\n")
    try:
      result = subprocess.run(
        [*settings["commands"]["apply_workspace_layout"], expression],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=settings["limits"]["command_timeout_seconds"],
      )
    except (OSError, subprocess.SubprocessError):
      return _report("apply_failed", "command_failure", settings)
    if result.returncode != settings["statuses"]["success"]:
      return _report("apply_failed", "command_failure", settings)

    layout_directory = _state_directory(settings)
    mode_file = layout_directory / f"{workspace_id}{settings['paths']['workspace_file_suffix']}"
    message_key = values["workspace_layout_notification"] if new_mode == values["tiling_modes"][0] else values["scrolling_layout_notification"]
    unsaved_key = values["workspace_layout_unsaved_notification"] if new_mode == values["tiling_modes"][0] else values["scrolling_layout_unsaved_notification"]
    try:
      if new_mode == _default_mode(settings):
        if mode_file.exists() or mode_file.is_symlink():
          mode_file.unlink()
      else:
        _write_state_file(mode_file, _workspace_layout_expression(workspace_id, new_mode, settings), settings)
    except OSError:
      _notify(unsaved_key, "toggle_unsaved", settings)
    else:
      _notify(message_key, "toggle_set", settings)
    _refresh_workspaces(settings)
    return settings["statuses"]["success"]
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError, re.error, subprocess.SubprocessError):
    try:
      return _report("configuration_failed", "configuration_error", _settings())
    except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
      return os.EX_CONFIG
