from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml

from arch.cli.lib.bounded import run_bounded


class StateSettings(TypedDict):
  default_directory: Path
  xdg_subdirectory: str
  files: dict[str, str]
  max_file_bytes: int
  directory_mode: int
  file_mode: int


class Settings(TypedDict):
  commands: dict[str, list[str]]
  timeouts: dict[str, int]
  cleanup_timeout_seconds: int
  max_output_bytes: int
  read_chunk_bytes: int
  on_battery_value: str
  actions: dict[str, str]
  fallback_profiles: dict[str, str]
  last_resort_profile: str
  state: StateSettings
  statuses: dict[str, int]
  messages: dict[str, str]


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError("configuration must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError("configuration text must be a non-empty string")
  return value


def _strings(value: object) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(part, str) and part for part in value):
    raise ValueError("command must be a non-empty list of strings")
  return cast(list[str], value)


def _positive_integer(value: object) -> int:
  if type(value) is not int or value <= 0:
    raise ValueError("configuration value must be a positive integer")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/powerprofiles-set.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  raw_commands = _mapping(document.get("commands"))
  raw_timeouts = _mapping(document.get("timeouts"))
  raw_actions = _mapping(document.get("actions"))
  raw_fallbacks = _mapping(document.get("fallback_profiles"))
  raw_state = _mapping(document.get("state"))
  raw_files = _mapping(raw_state.get("files"))
  raw_statuses = _mapping(document.get("statuses"))
  raw_messages = _mapping(document.get("messages"))

  commands = {name: _strings(value) for name, value in raw_commands.items()}
  timeouts = {name: _positive_integer(value) for name, value in raw_timeouts.items()}
  actions = {name: _text(value) for name, value in raw_actions.items()}
  fallbacks = {name: _text(value) for name, value in raw_fallbacks.items()}
  files = {name: _text(value) for name, value in raw_files.items()}
  statuses = {
    name: value
    for name, value in raw_statuses.items()
    if type(value) is int and 0 <= value <= 255
  }
  messages = {name: _text(value) for name, value in raw_messages.items()}
  if set(commands) != {"battery_state", "list_profiles", "set_profile", "refresh_shell"}:
    raise ValueError("commands must define every power profile operation")
  if set(timeouts) != set(commands):
    raise ValueError("timeouts must match configured commands")
  if set(actions) != {"autodetect", "ac", "battery"} or len(set(actions.values())) != len(actions):
    raise ValueError("actions must define unique autodetect, ac, and battery names")
  if set(fallbacks) != {actions["ac"], actions["battery"]}:
    raise ValueError("fallback profiles must be defined for ac and battery")
  if set(files) != set(fallbacks):
    raise ValueError("state files must be defined for ac and battery")
  if set(statuses) != {
    "success",
    "invalid_arguments",
    "profile_unavailable",
    "state_error",
    "timeout",
    "command_error",
    "signal_status_base",
  } or statuses.get("success") != 0 or any(
    value <= 0 for name, value in statuses.items() if name != "success"
  ):
    raise ValueError("statuses must define all operation results and a zero success code")
  mode_values = (raw_state.get("directory_mode"), raw_state.get("file_mode"))
  if any(type(mode) is not int or not 0 <= mode <= 0o777 for mode in mode_values):
    raise ValueError("state directory and file modes must be valid permission bits")

  return {
    "commands": commands,
    "timeouts": timeouts,
    "cleanup_timeout_seconds": _positive_integer(document.get("cleanup_timeout_seconds")),
    "max_output_bytes": _positive_integer(document.get("max_output_bytes")),
    "read_chunk_bytes": _positive_integer(document.get("read_chunk_bytes")),
    "on_battery_value": _text(document.get("on_battery_value")),
    "actions": actions,
    "fallback_profiles": fallbacks,
    "last_resort_profile": _text(document.get("last_resort_profile")),
    "state": {
      "default_directory": Path(_text(raw_state.get("default_directory"))).expanduser(),
      "xdg_subdirectory": _text(raw_state.get("xdg_subdirectory")),
      "files": files,
      "max_file_bytes": _positive_integer(raw_state.get("max_file_bytes")),
      "directory_mode": cast(int, mode_values[0]),
      "file_mode": cast(int, mode_values[1]),
    },
    "statuses": statuses,
    "messages": messages,
  }


def _run(settings: Settings, name: str, arguments: list[str] | None = None) -> bytes | None:
  return run_bounded(
    settings["commands"][name] + (arguments or []),
    timeout_seconds=settings["timeouts"][name],
    cleanup_timeout_seconds=settings["cleanup_timeout_seconds"],
    max_output_bytes=settings["max_output_bytes"],
    read_chunk_bytes=settings["read_chunk_bytes"],
  )


def _state_directory(settings: Settings) -> Path:
  state = settings["state"]
  xdg_home = os.environ.get("XDG_STATE_HOME")
  if xdg_home:
    return Path(xdg_home) / state["xdg_subdirectory"]
  return state["default_directory"]


def _read_preference(path: Path, maximum_bytes: int) -> str:
  try:
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
      contents = stream.read(maximum_bytes + 1)
  except OSError:
    return ""
  if len(contents) > maximum_bytes:
    return ""
  try:
    return contents.decode("ascii").strip()
  except UnicodeError:
    return ""


def _save_preference(path: Path, value: str, settings: Settings) -> None:
  state = settings["state"]
  path.parent.mkdir(mode=state["directory_mode"], parents=True, exist_ok=True)
  directory_info = path.parent.lstat()
  if not stat.S_ISDIR(directory_info.st_mode) or directory_info.st_uid != os.getuid():
    raise OSError("power profile state directory is not owned by the current user")

  descriptor, temporary_name = tempfile.mkstemp(dir=path.parent)
  temporary_path = Path(temporary_name)
  try:
    os.fchmod(descriptor, state["file_mode"])
    with os.fdopen(descriptor, "w", encoding="ascii") as stream:
      descriptor = -1
      stream.write(f"{value}\n")
      stream.flush()
      os.fsync(stream.fileno())
    os.replace(temporary_path, path)
  except OSError:
    if descriptor >= 0:
      os.close(descriptor)
    temporary_path.unlink(missing_ok=True)
    raise


def _profile_is_available(profile: str, profiles: list[str]) -> bool:
  return profile in profiles


def main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  actions = settings["actions"]
  if len(arguments) > 2:
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]
  action = arguments[0] if arguments and arguments[0] else actions["autodetect"]
  requested_profile = arguments[1] if len(arguments) > 1 else ""
  if action == actions["autodetect"]:
    try:
      battery_result = _run(settings, "battery_state")
    except OSError:
      battery_result = None
    action = (
      actions["battery"]
      if battery_result is not None and battery_result.decode("utf-8", errors="replace").strip() == settings["on_battery_value"]
      else actions["ac"]
    )
  elif action not in (actions["ac"], actions["battery"]):
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]

  try:
    profiles_result = _run(settings, "list_profiles")
  except OSError:
    profiles_result = None
  profiles = [] if profiles_result is None else profiles_result.decode("utf-8", errors="replace").splitlines()

  if requested_profile and not _profile_is_available(requested_profile, profiles):
    print(settings["messages"]["profile_unavailable"], file=sys.stderr)
    return settings["statuses"]["profile_unavailable"]

  state = settings["state"]
  state_path = _state_directory(settings) / state["files"][action]
  if requested_profile:
    profile = requested_profile
  else:
    profile = _read_preference(state_path, state["max_file_bytes"])
  if not _profile_is_available(profile, profiles):
    profile = settings["fallback_profiles"].get(action, settings["last_resort_profile"])
  if not _profile_is_available(profile, profiles):
    profile = settings["last_resort_profile"]

  try:
    result = subprocess.run(
      settings["commands"]["set_profile"] + [profile],
      check=False,
      stdout=subprocess.DEVNULL,
      timeout=settings["timeouts"]["set_profile"],
    )
  except subprocess.TimeoutExpired:
    print(settings["messages"]["timeout"], file=sys.stderr)
    return settings["statuses"]["timeout"]
  except OSError:
    print(settings["messages"]["command_error"], file=sys.stderr)
    return settings["statuses"]["command_error"]
  if result.returncode != settings["statuses"]["success"]:
    print(settings["messages"]["apply_failed"], file=sys.stderr)
    if result.returncode < settings["statuses"]["success"]:
      return settings["statuses"]["signal_status_base"] + abs(result.returncode)
    return result.returncode
  try:
    _run(settings, "refresh_shell")
  except OSError:
    pass
  if requested_profile:
    try:
      _save_preference(state_path, requested_profile, settings)
    except OSError:
      print(settings["messages"]["state_error"], file=sys.stderr)
      return settings["statuses"]["state_error"]
  return settings["statuses"]["success"]
