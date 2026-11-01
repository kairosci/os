from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  install_package: list[str]
  refresh_theme: list[str]
  theme_source: str
  theme_link: str
  config: str
  shell_rc: str
  config_contents: str
  shell_alias: str
  configuration_error: str
  operation_error: str
  installing: str
  success: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"Helix installer {label} must be a mapping")
  return cast(dict[str, object], value)


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
    raise TypeError(f"Helix installer {label} must be a non-empty string list")
  return cast(list[str], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"Helix installer {label} must be a non-empty string")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"Helix installer {label} must be an exit status")
  return value


def _settings(document: dict[str, object]) -> Settings:
  commands = _mapping(document.get("commands"), "commands")
  paths = _mapping(document.get("paths"), "paths")
  contents = _mapping(document.get("contents"), "contents")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  return {
    "install_package": _strings(commands.get("install_package"), "package command"),
    "refresh_theme": _strings(commands.get("refresh_theme"), "theme refresh command"),
    "theme_source": _text(paths.get("theme_source"), "theme source path"),
    "theme_link": _text(paths.get("theme_link"), "theme link path"),
    "config": _text(paths.get("config"), "config path"),
    "shell_rc": _text(paths.get("shell_rc"), "shell rc path"),
    "config_contents": _text(contents.get("config"), "config contents"),
    "shell_alias": _text(contents.get("shell_alias"), "shell alias"),
    "configuration_error": _text(messages.get("configuration_error"), "configuration error message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "installing": _text(messages.get("installing"), "progress message"),
    "success": _status(statuses.get("success"), "success status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
  }


def _home_path(home: Path, relative: str) -> Path:
  path = Path(relative)
  if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
    raise ValueError("configured user path must stay below the home directory")
  return home / path


def _seed_config(path: Path, contents: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  try:
    with path.open("x", encoding="utf-8") as config_file:
      config_file.write(contents)
  except FileExistsError:
    return


def _set_theme_link(path: Path, target: Path) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  with tempfile.TemporaryDirectory(dir=path.parent) as temporary_directory:
    temporary_link = Path(temporary_directory) / path.name
    temporary_link.symlink_to(target)
    os.replace(temporary_link, path)


def _ensure_alias(path: Path, alias: str) -> None:
  if path.is_file() and alias in path.read_text(encoding="utf-8").splitlines():
    return
  with path.open("a", encoding="utf-8") as shell_rc:
    if path.stat().st_size > 0 and not path.read_bytes().endswith(b"\n"):
      shell_rc.write("\n")
    shell_rc.write(f"{alias}\n")


def helix_main() -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load((root / "data/cli/install-editor-helix.yml").read_text(encoding="utf-8"))
    document = _mapping(raw, "configuration")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"), "configuration error message")
    settings = _settings(document)
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(configuration_error.format(error=error) if configuration_error else error, file=sys.stderr)
    return 1

  print(settings["installing"], flush=True)
  try:
    result = subprocess.run(settings["install_package"], check=False)
    if result.returncode != settings["success"]:
      return result.returncode

    home = Path(os.environ["HOME"])
    theme_source = _home_path(home, settings["theme_source"])
    if not theme_source.exists():
      refreshed = subprocess.run(settings["refresh_theme"], check=False)
      if refreshed.returncode != settings["success"]:
        return refreshed.returncode
    if not theme_source.is_file():
      raise FileNotFoundError(theme_source)

    _set_theme_link(_home_path(home, settings["theme_link"]), theme_source)
    _seed_config(_home_path(home, settings["config"]), settings["config_contents"])
    _ensure_alias(_home_path(home, settings["shell_rc"]), settings["shell_alias"])
  except (OSError, subprocess.SubprocessError, ValueError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
