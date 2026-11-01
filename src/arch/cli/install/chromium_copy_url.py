from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Manifest(TypedDict):
  name: str
  description: str
  type: str
  allowed_origins: list[str]


class Settings(TypedDict):
  host_name: str
  host_source: str
  manifest: Manifest
  native_messaging_directory: str
  browser_profiles: list[str]
  file_mode: int
  configuration_error: str
  operation_error: str
  success: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"Copy URL host {label} must be a mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"Copy URL host {label} must be non-empty text")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"Copy URL host {label} must be an exit status")
  return value


def _relative(value: object, label: str) -> str:
  text = _text(value, label)
  path = Path(text)
  if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
    raise ValueError(f"Copy URL host {label} must be a relative path without traversal")
  return text


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
    raise TypeError(f"Copy URL host {label} must be a non-empty string list")
  return cast(list[str], value)


def _settings(document: dict[str, object]) -> Settings:
  host_name = _text(document.get("host_name"), "host name")
  manifest = _mapping(document.get("manifest"), "manifest")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  allowed_origins = _strings(manifest.get("allowed_origins"), "allowed origins")
  manifest_name = _text(manifest.get("name"), "manifest name")
  if manifest_name != host_name or "/" in host_name or "\\" in host_name:
    raise ValueError("Copy URL host manifest name must match its path-safe host name")
  file_mode = document.get("file_mode")
  if type(file_mode) is not int or not 0 <= file_mode <= 0o777:
    raise TypeError("Copy URL host file mode must be a permission mode")
  return {
    "host_name": host_name,
    "host_source": _relative(document.get("host_source"), "host source"),
    "manifest": {
      "name": manifest_name,
      "description": _text(manifest.get("description"), "manifest description"),
      "type": _text(manifest.get("type"), "manifest type"),
      "allowed_origins": allowed_origins,
    },
    "native_messaging_directory": _relative(document.get("native_messaging_directory"), "manifest directory"),
    "browser_profiles": [_relative(item, "browser profile") for item in _strings(document.get("browser_profiles"), "browser profiles")],
    "file_mode": file_mode,
    "configuration_error": _text(messages.get("configuration_error"), "configuration error message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "success": _status(statuses.get("success"), "success status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
  }


def _atomic_write(path: Path, contents: str, mode: int) -> None:
  target = path.resolve()
  target.parent.mkdir(parents=True, exist_ok=True)
  try:
    mode = stat.S_IMODE(target.stat().st_mode)
  except FileNotFoundError:
    pass
  descriptor, temporary = tempfile.mkstemp(dir=target.parent)
  temporary_path = Path(temporary)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      os.fchmod(output.fileno(), mode)
      output.write(contents)
      output.flush()
      os.fsync(output.fileno())
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)


def install_chromium_copy_url_main() -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load((root / "data/cli/install-chromium-copy-url.yml").read_text(encoding="utf-8"))
    document = _mapping(raw, "configuration")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"), "configuration error message")
    settings = _settings(document)
  except (KeyError, OSError, RuntimeError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(configuration_error.format(error=error) if configuration_error else error, file=sys.stderr)
    return 1

  try:
    root_path = root.resolve(strict=True)
    host_path = (root_path / settings["host_source"]).resolve(strict=True)
    if not host_path.is_relative_to(root_path):
      raise ValueError("native host source resolves outside the Arch root")
    if not host_path.is_file() or not os.access(host_path, os.X_OK):
      raise OSError(f"native host is not an executable file: {host_path}")
    manifest = {**settings["manifest"], "path": str(host_path)}
    contents = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    home = Path(os.environ["HOME"])
    for profile in settings["browser_profiles"]:
      destination = home / profile / settings["native_messaging_directory"] / f"{settings['host_name']}.json"
      _atomic_write(destination, contents, settings["file_mode"])
  except (KeyError, OSError, RuntimeError, ValueError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
