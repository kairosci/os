from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml
from arch.cli.lib.bounded import run_bounded


class DeviceNotification(TypedDict):
  icon: str
  enabled_key: str
  disabled_key: str


class Settings(TypedDict):
  commands: dict[str, list[str]]
  state_directory: str
  disabled_name_suffix: str
  temporary_prefix: str
  kinds: list[str]
  actions: dict[str, str]
  lua_device_call: str
  lua_true: str
  lua_false: str
  notifications: dict[str, DeviceNotification]
  device_timeout: int
  command_timeout: int
  cleanup_timeout: int
  maximum_device_output: int
  read_chunk_bytes: int
  usage: str
  no_device: str
  invalid_device_name: str
  command_error: str
  success: int
  invalid_arguments: int
  command_error_status: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"{label} must be non-empty text")
  return value


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"{label} must be a non-empty list of strings")
  return cast(list[str], value)


def _positive(value: object, label: str) -> int:
  if type(value) is not int or value <= 0:
    raise ValueError(f"{label} must be a positive integer")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise ValueError(f"{label} must be an exit status")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/input-device-toggle.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "configuration")
  commands = _mapping(document.get("commands"), "commands")
  paths = _mapping(document.get("paths"), "paths")
  values = _mapping(document.get("values"), "values")
  actions = _mapping(values.get("actions"), "values.actions")
  notifications = _mapping(document.get("notifications"), "notifications")
  limits = _mapping(document.get("limits"), "limits")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")

  state_directory = _text(paths.get("home_relative_state_directory"), "paths.home_relative_state_directory")
  state_path = Path(state_directory)
  if state_path.is_absolute() or ".." in state_path.parts:
    raise ValueError("state directory must stay under HOME")

  device_notifications: dict[str, DeviceNotification] = {}
  kinds = _strings(values.get("kinds"), "values.kinds")
  for kind in kinds:
    item = _mapping(notifications.get(kind), f"notifications.{kind}")
    device_notifications[kind] = {
      "icon": _text(item.get("icon"), f"notifications.{kind}.icon"),
      "enabled_key": _text(item.get("enabled_key"), f"notifications.{kind}.enabled_key"),
      "disabled_key": _text(item.get("disabled_key"), f"notifications.{kind}.disabled_key"),
    }
  if len(set(kinds)) != len(kinds):
    raise ValueError("values.kinds must be unique")

  return {
    "commands": {
      name: _strings(commands.get(name), f"commands.{name}")
      for name in ("device_name", "apply_device", "localize", "osd")
    },
    "state_directory": state_directory,
    "disabled_name_suffix": _text(paths.get("disabled_name_suffix"), "paths.disabled_name_suffix"),
    "temporary_prefix": _text(paths.get("temporary_prefix"), "paths.temporary_prefix"),
    "kinds": kinds,
    "actions": {
      name: _text(actions.get(name), f"values.actions.{name}")
      for name in ("enable", "disable", "toggle")
    },
    "lua_device_call": _text(values.get("lua_device_call"), "values.lua_device_call"),
    "lua_true": _text(values.get("lua_true"), "values.lua_true"),
    "lua_false": _text(values.get("lua_false"), "values.lua_false"),
    "notifications": device_notifications,
    "device_timeout": _positive(limits.get("device_timeout_seconds"), "limits.device_timeout_seconds"),
    "command_timeout": _positive(limits.get("command_timeout_seconds"), "limits.command_timeout_seconds"),
    "cleanup_timeout": _positive(limits.get("cleanup_timeout_seconds"), "limits.cleanup_timeout_seconds"),
    "maximum_device_output": _positive(limits.get("maximum_device_output_bytes"), "limits.maximum_device_output_bytes"),
    "read_chunk_bytes": _positive(limits.get("read_chunk_bytes"), "limits.read_chunk_bytes"),
    "usage": _text(messages.get("usage"), "messages.usage"),
    "no_device": _text(messages.get("no_device"), "messages.no_device"),
    "invalid_device_name": _text(messages.get("invalid_device_name"), "messages.invalid_device_name"),
    "command_error": _text(messages.get("command_error"), "messages.command_error"),
    "success": _status(statuses.get("success"), "statuses.success"),
    "invalid_arguments": _status(statuses.get("invalid_arguments"), "statuses.invalid_arguments"),
    "command_error_status": _status(statuses.get("command_error"), "statuses.command_error"),
  }


def _name_file(kind: str, settings: Settings) -> Path:
  return Path(os.environ["HOME"]) / settings["state_directory"] / f"{kind}{settings['disabled_name_suffix']}"


def _ensure_state_directory(path: Path) -> None:
  home = Path(os.environ["HOME"])
  relative = path.relative_to(home)
  current = home
  for component in relative.parts:
    current = current / component
    try:
      mode = current.lstat().st_mode
    except FileNotFoundError:
      current.mkdir(mode=0o700)
      mode = current.lstat().st_mode
    if not stat.S_ISDIR(mode):
      raise OSError("input-device state path contains a non-directory")


def _device_name(kind: str, settings: Settings) -> str | None:
  command = [*settings["commands"]["device_name"], kind]
  try:
    output = run_bounded(
      command,
      timeout_seconds=settings["device_timeout"],
      cleanup_timeout_seconds=settings["cleanup_timeout"],
      max_output_bytes=settings["maximum_device_output"],
      read_chunk_bytes=settings["read_chunk_bytes"],
    )
  except OSError:
    return None
  if output is None:
    return None
  try:
    name = output.decode("utf-8", errors="strict").rstrip("\n")
  except UnicodeError:
    raise ValueError("device name is not valid UTF-8") from None
  if not name or any(ord(character) < 32 or ord(character) == 127 for character in name):
    raise ValueError("device name contains control characters")
  return name


def _disabled(path: Path) -> bool:
  try:
    mode = path.lstat().st_mode
  except FileNotFoundError:
    return False
  if not stat.S_ISREG(mode):
    raise OSError("disabled device state is not a regular file")
  return True


def _apply_device(name: str, enabled: bool, settings: Settings) -> bool:
  lua_enabled = settings["lua_true"] if enabled else settings["lua_false"]
  lua_name = name.replace("\\", "\\\\").replace('"', '\\"')
  expression = settings["lua_device_call"].format(name=lua_name, enabled=lua_enabled)
  try:
    result = subprocess.run(
      [*settings["commands"]["apply_device"], expression],
      check=False,
      stdout=subprocess.DEVNULL,
      timeout=settings["command_timeout"],
    )
  except (OSError, subprocess.TimeoutExpired):
    return False
  return result.returncode == settings["success"]


def _store_name(path: Path, name: str, settings: Settings) -> bool:
  temporary: Path | None = None
  try:
    _ensure_state_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=settings["temporary_prefix"], dir=path.parent)
    temporary = Path(temporary_name)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
      stream.write(f"{name}\n")
      stream.flush()
      os.fsync(stream.fileno())
    os.replace(temporary, path)
  except OSError:
    if temporary is not None:
      temporary.unlink(missing_ok=True)
    return False
  return True


def _notify(kind: str, enabled: bool, settings: Settings) -> bool:
  notification = settings["notifications"][kind]
  localization_key = notification["enabled_key"] if enabled else notification["disabled_key"]
  try:
    message = run_bounded(
      [*settings["commands"]["localize"], localization_key],
      timeout_seconds=settings["command_timeout"],
      cleanup_timeout_seconds=settings["cleanup_timeout"],
      max_output_bytes=settings["maximum_device_output"],
      read_chunk_bytes=settings["read_chunk_bytes"],
    )
  except OSError:
    return False
  if message is None:
    return False
  text = message.decode("utf-8", errors="surrogateescape").rstrip("\n")
  try:
    result = subprocess.run(
      [*settings["commands"]["osd"], notification["icon"], "-m", text],
      check=False,
      timeout=settings["command_timeout"],
    )
  except (OSError, subprocess.TimeoutExpired):
    return False
  return result.returncode == settings["success"]


def input_device_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  if not 1 <= len(arguments) <= 2:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]
  kind = arguments[0]
  actions = settings["actions"]
  action = arguments[1] if len(arguments) == 2 else actions["toggle"]
  if kind not in settings["kinds"] or action not in actions.values():
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]

  path = _name_file(kind, settings)
  try:
    is_disabled = _disabled(path)
  except OSError:
    print(settings["command_error"].format(kind=kind), file=sys.stderr)
    return settings["command_error_status"]
  enabling = action == actions["enable"] or (action == actions["toggle"] and is_disabled)
  try:
    device_name = _device_name(kind, settings)
  except ValueError:
    print(settings["invalid_device_name"].format(kind=kind), file=sys.stderr)
    return settings["invalid_arguments"]

  if enabling:
    try:
      path.unlink(missing_ok=True)
    except OSError:
      print(settings["command_error"].format(kind=kind), file=sys.stderr)
      return settings["command_error_status"]
    if device_name is None:
      print(settings["no_device"].format(kind=kind), file=sys.stderr)
      return settings["invalid_arguments"]
  elif device_name is None:
    print(settings["no_device"].format(kind=kind), file=sys.stderr)
    return settings["invalid_arguments"]

  if not _apply_device(device_name, enabling, settings):
    print(settings["command_error"].format(kind=kind), file=sys.stderr)
    return settings["command_error_status"]
  if not enabling and not _store_name(path, device_name, settings):
    print(settings["command_error"].format(kind=kind), file=sys.stderr)
    return settings["command_error_status"]
  if not _notify(kind, enabling, settings):
    print(settings["command_error"].format(kind=kind), file=sys.stderr)
    return settings["command_error_status"]
  return settings["success"]
