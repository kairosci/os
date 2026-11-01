from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml


class UserFile(TypedDict):
  path: str
  mode: int
  contents: str


class Settings(TypedDict):
  install_package: list[str]
  apply_theme: list[str]
  launch_application: list[str]
  files: list[UserFile]
  configuration_error: str
  operation_error: str
  installing: str
  success: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"VS Code installer {label} must be a mapping")
  return cast(dict[str, object], value)


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
    raise TypeError(f"VS Code installer {label} must be a non-empty string list")
  return cast(list[str], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"VS Code installer {label} must be a non-empty string")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"VS Code installer {label} must be an exit status")
  return value


def _user_files(value: object) -> list[UserFile]:
  if not isinstance(value, list) or not value:
    raise TypeError("VS Code installer files must be a non-empty list")
  files: list[UserFile] = []
  for item in value:
    entry = _mapping(item, "file")
    path = _text(entry.get("path"), "user file path")
    mode = entry.get("mode")
    contents = entry.get("contents")
    if type(mode) is not int or not 0 <= mode <= 0o777:
      raise TypeError("VS Code installer file mode must be a permission mode")
    if not isinstance(contents, str):
      raise TypeError("VS Code installer file contents must be text")
    files.append({"path": path, "mode": mode, "contents": contents})
  return files


def _settings(document: dict[str, object]) -> Settings:
  commands = _mapping(document.get("commands"), "commands")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  return {
    "install_package": _strings(commands.get("install_package"), "package command"),
    "apply_theme": _strings(commands.get("apply_theme"), "theme command"),
    "launch_application": _strings(commands.get("launch_application"), "launch command"),
    "files": _user_files(document.get("files")),
    "configuration_error": _text(messages.get("configuration_error"), "configuration error message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "installing": _text(messages.get("installing"), "progress message"),
    "success": _status(statuses.get("success"), "success status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
  }


def _user_path(home: Path, relative: str) -> Path:
  path = Path(relative)
  if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
    raise ValueError("configured user path must stay below the home directory")
  home_path = home.resolve()
  resolved = (home_path / path).resolve()
  if not resolved.is_relative_to(home_path):
    raise ValueError("configured user path resolves outside the home directory")
  return resolved


def _write_user_file(path: Path, contents: str, mode: int) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  try:
    mode = stat.S_IMODE(path.stat().st_mode)
  except FileNotFoundError:
    pass
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


def vscode_main() -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load((root / "data/cli/install-editor-vscode.yml").read_text(encoding="utf-8"))
    document = _mapping(raw, "configuration")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"), "configuration error message")
    settings = _settings(document)
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(configuration_error.format(error=error) if configuration_error else error, file=sys.stderr)
    return 1

  print(settings["installing"], flush=True)
  try:
    installed = subprocess.run(settings["install_package"], check=False)
    if installed.returncode != settings["success"]:
      return installed.returncode

    home = Path(os.environ["HOME"])
    for user_file in settings["files"]:
      _write_user_file(_user_path(home, user_file["path"]), user_file["contents"], user_file["mode"])

    themed = subprocess.run(settings["apply_theme"], check=False)
    if themed.returncode != settings["success"]:
      return themed.returncode

    subprocess.Popen(
      settings["launch_application"],
      stdin=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      start_new_session=True,
    )
  except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
