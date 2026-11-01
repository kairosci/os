from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml

from arch.cli.chromium.features import ensure_chromium_flags
from arch.cli.chromium.features import load_settings as load_chromium_feature_settings


class Settings(TypedDict):
  hardware_check: list[str]
  mpv_file: str
  mpv_comment: str
  mpv_option: str
  mpv_value: str
  mpv_default_profile: str
  mpv_file_mode: int
  chromium_feature: str
  chromium_angle_argument: str
  configuration_error: str
  operation_error: str
  success: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"video decode {label} must be a mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"video decode {label} must be non-empty text")
  return value


def _relative(value: object, label: str) -> str:
  text = _text(value, label)
  path = Path(text)
  if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
    raise ValueError(f"video decode {label} must be a relative path without traversal")
  return text


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"video decode {label} must be an exit status")
  return value


def _settings(document: dict[str, object]) -> Settings:
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  hardware_check = document.get("hardware_check")
  file_mode = document.get("mpv_file_mode")
  angle_argument = _text(document.get("chromium_angle_argument"), "Chromium ANGLE argument")
  if not isinstance(hardware_check, list) or not hardware_check or not all(
    isinstance(part, str) and part for part in hardware_check
  ):
    raise TypeError("video decode hardware check must be a non-empty argument list")
  if type(file_mode) is not int or not 0 <= file_mode <= 0o777:
    raise TypeError("video decode mpv file mode must be a permission mode")
  if not angle_argument.startswith("--") or "=" not in angle_argument:
    raise ValueError("video decode Chromium ANGLE argument must be a switch with a value")
  return {
    "hardware_check": cast(list[str], hardware_check),
    "mpv_file": _relative(document.get("mpv_file"), "mpv file"),
    "mpv_comment": _text(document.get("mpv_comment"), "mpv comment"),
    "mpv_option": _text(document.get("mpv_option"), "mpv option"),
    "mpv_value": _text(document.get("mpv_value"), "mpv value"),
    "mpv_default_profile": _text(document.get("mpv_default_profile"), "mpv default profile"),
    "mpv_file_mode": file_mode,
    "chromium_feature": _text(document.get("chromium_feature"), "Chromium feature"),
    "chromium_angle_argument": angle_argument,
    "configuration_error": _text(messages.get("configuration_error"), "configuration error message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "success": _status(statuses.get("success"), "success status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
  }


def _target(home: Path, relative: str) -> Path:
  target = (home / relative).resolve(strict=False)
  if not target.is_relative_to(home):
    raise ValueError("video decode configuration resolves outside the home directory")
  return target


def _line_ending(contents: str) -> str:
  return "\r\n" if "\r\n" in contents else "\n"


def _has_global_option(contents: str, settings: Settings) -> bool:
  global_options = True
  for line in contents.splitlines():
    value = line.partition("#")[0].strip()
    if value.startswith("[") and "]" in value:
      profile = value[1 : value.index("]")].strip()
      global_options = profile == settings["mpv_default_profile"]
      continue
    if global_options and "=" in value and value.partition("=")[0].strip() == settings["mpv_option"]:
      return True
  return False


def _atomic_write(target: Path, contents: str, file_mode: int) -> None:
  target.parent.mkdir(parents=True, exist_ok=True)
  try:
    mode = target.stat().st_mode
  except FileNotFoundError:
    mode = file_mode
  else:
    if not os.access(target, os.W_OK):
      raise PermissionError("mpv configuration is not writable")
  descriptor, temporary = tempfile.mkstemp(dir=target.parent)
  temporary_path = Path(temporary)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as output:
      os.fchmod(output.fileno(), mode & 0o777)
      output.write(contents)
      output.flush()
      os.fsync(output.fileno())
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)


def _setup_mpv(home: Path, settings: Settings) -> None:
  target = _target(home, settings["mpv_file"])
  if target.is_file():
    with target.open("r", encoding="utf-8", newline="") as source:
      contents = source.read()
  else:
    contents = ""
  option = f"{settings['mpv_option']}={settings['mpv_value']}"
  if contents and _has_global_option(contents, settings):
    return
  newline = _line_ending(contents)
  prefix = f"{settings['mpv_comment']}{newline}{option}{newline}"
  _atomic_write(target, prefix + contents, settings["mpv_file_mode"])


def _setup_chromium(root: Path, home: Path, settings: Settings) -> None:
  feature_settings = load_chromium_feature_settings(root)
  ensure_chromium_flags(
    home,
    feature_settings,
    settings["chromium_feature"],
    [settings["chromium_angle_argument"]],
  )


def install_video_decode_main() -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load((root / "data/cli/install-video-decode.yml").read_text(encoding="utf-8"))
    document = _mapping(raw, "configuration")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"), "configuration error message")
    settings = _settings(document)
  except (KeyError, OSError, RuntimeError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(configuration_error.format(error=error) if configuration_error else error, file=sys.stderr)
    return 1

  try:
    hardware = subprocess.run(settings["hardware_check"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  except OSError as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  if hardware.returncode != 0:
    return settings["success"]

  try:
    home = Path(os.environ["HOME"]).resolve(strict=True)
  except (KeyError, OSError, RuntimeError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]

  status = settings["success"]
  try:
    _setup_mpv(home, settings)
  except (OSError, RuntimeError, ValueError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    status = settings["operation_failed"]
  try:
    _setup_chromium(root, home, settings)
  except (OSError, RuntimeError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    status = settings["operation_failed"]
  return status
