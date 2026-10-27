from __future__ import annotations

import fcntl
import os
from pathlib import Path

import yaml


def _settings() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load(
    (root / "data/cli/background-session-mark.yml").read_text(encoding="utf-8")
  )
  if not isinstance(settings, dict):
    raise ValueError("invalid background session marker configuration")
  return settings


def main() -> int:
  settings = _settings()
  session_id = next(
    (os.environ[name] for name in settings["session_environment"] if os.environ.get(name)),
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
