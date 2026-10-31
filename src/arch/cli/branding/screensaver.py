from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  commands: dict[str, list[str]]
  user_text: str
  default_text: str
  image_localization_key: str
  image_extensions: list[str]
  actions: dict[str, str]
  usage: str
  command_error: str
  success: int
  invalid_arguments: int
  command_error_status: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _required_text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"{label} must be non-empty text")
  return value


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"{label} must be a list of non-empty strings")
  return cast(list[str], value)


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise ValueError(f"{label} must be an exit status")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/branding.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "configuration")
  raw_commands = _mapping(document.get("commands"), "commands")
  raw_paths = _mapping(document.get("paths"), "paths")
  raw_values = _mapping(document.get("values"), "values")
  raw_actions = _mapping(raw_values.get("actions"), "values.actions")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")

  def command(key: str) -> list[str]:
    return _strings(raw_commands.get(key), f"commands.{key}")

  def text(section: dict[str, object], key: str, label: str) -> str:
    return _required_text(section.get(key), f"{label}.{key}")

  actions = {
    name: _required_text(raw_actions.get(name), f"values.actions.{name}")
    for name in ("image", "text", "reset")
  }
  if len(set(actions.values())) != len(actions):
    raise ValueError("values.actions must be unique")

  return {
    "commands": {
      name: command(name)
      for name in ("file_select", "transcode_ascii", "launch_screensaver", "launch_editor", "localize")
    },
    "user_text": text(raw_paths, "user_text", "paths"),
    "default_text": text(raw_paths, "default_text", "paths"),
    "image_localization_key": text(raw_values, "image_localization_key", "values"),
    "image_extensions": _strings(raw_values.get("image_extensions"), "values.image_extensions"),
    "actions": actions,
    "usage": text(messages, "usage", "messages"),
    "command_error": text(messages, "command_error", "messages"),
    "success": _status(statuses.get("success"), "statuses.success"),
    "invalid_arguments": _status(statuses.get("invalid_arguments"), "statuses.invalid_arguments"),
    "command_error_status": _status(statuses.get("command_error"), "statuses.command_error"),
  }


def _run(command: list[str], *, capture: bool = False, quiet: bool = False) -> subprocess.CompletedProcess[bytes] | None:
  try:
    return subprocess.run(
      command,
      check=False,
      stdout=subprocess.PIPE if capture else subprocess.DEVNULL if quiet else None,
      stderr=subprocess.DEVNULL if quiet else None,
    )
  except OSError:
    return None


def _screensaver(settings: Settings) -> int:
  result = _run(settings["commands"]["launch_screensaver"], quiet=True)
  if result is None:
    return settings["command_error_status"]
  return result.returncode


def _image(settings: Settings, home: Path) -> int:
  localized = _run(
    [*settings["commands"]["localize"], settings["image_localization_key"]], capture=True
  )
  if localized is None or localized.returncode != settings["success"]:
    return settings["command_error_status"]
  title = localized.stdout.decode("utf-8", errors="surrogateescape").rstrip("\n")
  selection = _run(
    [
      *settings["commands"]["file_select"],
      title,
      *settings["image_extensions"],
    ],
    capture=True,
  )
  if selection is None:
    return settings["command_error_status"]
  if selection.returncode != settings["success"]:
    return selection.returncode
  image = selection.stdout.decode("utf-8", errors="surrogateescape").rstrip("\n")
  if not image:
    return settings["success"]
  target = home / settings["user_text"]
  converted = _run([*settings["commands"]["transcode_ascii"], image, str(target)])
  if converted is None:
    return settings["success"]
  if converted.returncode == settings["success"]:
    return _screensaver(settings)
  return settings["success"]


def _edit_text(settings: Settings, home: Path) -> int:
  result = _run([*settings["commands"]["launch_editor"], str(home / settings["user_text"])], quiet=True)
  if result is None:
    return settings["command_error_status"]
  if result.returncode == settings["success"]:
    return _screensaver(settings)
  return result.returncode


def _reset(settings: Settings, root: Path, home: Path) -> int:
  try:
    shutil.copyfile(root / settings["default_text"], home / settings["user_text"])
  except OSError:
    return settings["command_error_status"]
  return _screensaver(settings)


def screensaver_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  if len(arguments) != 1 or arguments[0] not in settings["actions"].values():
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]

  root = Path(os.environ["AP"])
  home = Path(os.environ["HOME"])
  action = arguments[0]
  if action == settings["actions"]["image"]:
    result = _image(settings, home)
  elif action == settings["actions"]["text"]:
    result = _edit_text(settings, home)
  elif action == settings["actions"]["reset"]:
    result = _reset(settings, root, home)
  else:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]
  if result == settings["command_error_status"]:
    print(settings["command_error"], file=sys.stderr)
  return result
