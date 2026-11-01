from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  flags_file: str
  flags: list[str]
  installing: str
  ready: str
  configuration_error: str
  operation_error: str
  success: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"Chromium Google account {label} must be a mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"Chromium Google account {label} must be non-empty text")
  return value


def _relative(value: object, label: str) -> str:
  text = _text(value, label)
  path = Path(text)
  if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
    raise ValueError(f"Chromium Google account {label} must be a relative path without traversal")
  return text


def _settings(document: dict[str, object]) -> Settings:
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  flags = document.get("flags")
  if not isinstance(flags, list) or not flags or not all(
    isinstance(flag, str) and flag and "\n" not in flag and "\r" not in flag for flag in flags
  ):
    raise TypeError("Chromium Google account flags must be non-empty single-line text")
  success = statuses.get("success")
  operation_failed = statuses.get("operation_failed")
  if type(success) is not int or not 0 <= success <= 255:
    raise TypeError("Chromium Google account success status must be an exit status")
  if type(operation_failed) is not int or not 0 <= operation_failed <= 255:
    raise TypeError("Chromium Google account failure status must be an exit status")
  return {
    "flags_file": _relative(document.get("flags_file"), "flags file"),
    "flags": cast(list[str], flags),
    "installing": _text(messages.get("installing"), "install message"),
    "ready": _text(messages.get("ready"), "ready message"),
    "configuration_error": _text(messages.get("configuration_error"), "configuration error message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "success": success,
    "operation_failed": operation_failed,
  }


def _atomic_write(path: Path, contents: str, mode: int) -> None:
  descriptor, temporary = tempfile.mkstemp(dir=path.parent)
  temporary_path = Path(temporary)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      os.fchmod(output.fileno(), mode)
      output.write(contents)
      output.flush()
      os.fsync(output.fileno())
    os.replace(temporary_path, path)
  finally:
    temporary_path.unlink(missing_ok=True)


def install_chromium_google_account_main() -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load(
      (root / "data/cli/install-chromium-google-account.yml").read_text(encoding="utf-8")
    )
    document = _mapping(raw, "configuration")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"), "configuration error message")
    settings = _settings(document)
  except (KeyError, OSError, RuntimeError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(configuration_error.format(error=error) if configuration_error else error, file=sys.stderr)
    return 1

  try:
    home = Path(os.environ["HOME"]).resolve(strict=True)
    flags_path = home / settings["flags_file"]
    if not flags_path.is_file():
      return settings["success"]
    target = flags_path.resolve(strict=True)
    if not target.is_relative_to(home):
      raise ValueError("Chromium flags file resolves outside the home directory")
    original = target.read_text(encoding="utf-8")
    existing = set(original.splitlines())
    missing = [flag for flag in settings["flags"] if flag not in existing]
    print(settings["installing"])
    if missing:
      contents = original
      if contents and not contents.endswith(("\n", "\r")):
        contents += "\n"
      contents += "\n".join(missing) + "\n"
      mode = stat.S_IMODE(target.stat().st_mode)
      _atomic_write(target, contents, mode)
    print(settings["ready"])
  except (KeyError, OSError, RuntimeError, UnicodeError, ValueError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
