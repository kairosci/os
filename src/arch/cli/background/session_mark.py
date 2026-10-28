from __future__ import annotations

import fcntl
import os
from pathlib import Path
import sys
from typing import TypedDict

import yaml


class Settings(TypedDict):
  default_state_home: str
  state_directory: str
  marker_filename: str
  lock_filename: str
  session_environment: list[str]
  file_mode: str


def _text(value: object, name: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid background session marker configuration: {name} must be a string")
  return value


def _settings() -> Settings:
  root = Path(os.environ["ARCH_PATH"])
  raw: object = yaml.safe_load(
    (root / "data/cli/background-session-mark.yml").read_text(encoding="utf-8")
  )
  if not isinstance(raw, dict):
    raise ValueError("invalid background session marker configuration: expected a mapping")

  values = {key: value for key, value in raw.items()}
  session_environment = values.get("session_environment")
  if not isinstance(session_environment, list) or not all(
    isinstance(name, str) for name in session_environment
  ):
    raise ValueError(
      "invalid background session marker configuration: session_environment must be a list of strings"
    )
  return {
    "default_state_home": _text(values.get("default_state_home"), "default_state_home"),
    "state_directory": _text(values.get("state_directory"), "state_directory"),
    "marker_filename": _text(values.get("marker_filename"), "marker_filename"),
    "lock_filename": _text(values.get("lock_filename"), "lock_filename"),
    "session_environment": [name for name in session_environment if isinstance(name, str)],
    "file_mode": _text(values.get("file_mode"), "file_mode"),
  }


def main() -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load background session marker configuration: {error}", file=sys.stderr)
    return 1
  session_id = next(
    (os.environ[name] for name in settings["session_environment"] if os.environ.get(name, "") != ""),
    None,
  )
  if session_id is None:
    return 0

  state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / settings["default_state_home"]))
  state_directory = state_home / settings["state_directory"]
  state_directory.mkdir(parents=True, exist_ok=True)
  if state_directory.is_symlink() or not state_directory.is_dir():
    raise NotADirectoryError(state_directory)

  mode = int(settings["file_mode"], 8)
  lock_path = state_directory / settings["lock_filename"]
  descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, mode)
  try:
    os.fchmod(descriptor, mode)
    fcntl.flock(descriptor, fcntl.LOCK_EX)
    marker = state_directory / settings["marker_filename"]
    try:
      if marker.is_file() and marker.read_text(encoding="utf-8").rstrip("\n") == session_id:
        return 0
    except FileNotFoundError:
      pass

    marker_descriptor = os.open(
      marker,
      os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
      mode,
    )
    try:
      os.fchmod(marker_descriptor, mode)
      with os.fdopen(marker_descriptor, "w", encoding="utf-8", closefd=False) as output:
        output.write(f"{session_id}\n")
        output.flush()
        os.fsync(output.fileno())
    finally:
      os.close(marker_descriptor)
  finally:
    os.close(descriptor)
  return 0
