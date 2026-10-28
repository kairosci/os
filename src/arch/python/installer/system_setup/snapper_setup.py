from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal, TypedDict

import yaml


class PathSetting(TypedDict):
  default: str
  environment_override: str


class Paths(TypedDict):
  config: PathSetting
  conf: PathSetting
  template: PathSetting


class TestMode(TypedDict):
  environment_variable: str
  disabled_value: str
  enabled_value: str


class Commands(TypedDict):
  create_config_primary: list[str]
  create_config_fallback: list[str]
  disable_timeline: list[list[str]]
  enable_cleanup: list[list[str]]
  disable_legacy_snapshot_sync: list[list[str]]


class Settings(TypedDict):
  paths: Paths
  directory_mode: str
  file_mode: str
  config_file_contents: str
  test_mode: TestMode
  commands: Commands


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"Snapper setup {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"Snapper setup {label} must be a string")
  return value


def _mode(value: object, label: str) -> str:
  mode = _text(value, label)
  try:
    parsed = int(mode, 8)
  except ValueError as error:
    raise ValueError(f"Snapper setup {label} must be an octal mode") from error
  if not 0 <= parsed <= 0o7777:
    raise ValueError(f"Snapper setup {label} is outside the supported mode range")
  return mode


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list):
    raise TypeError(f"Snapper setup {label} must be a list")
  return [_text(item, f"{label} item") for item in value]


def _command_groups(value: object, label: str) -> list[list[str]]:
  if not isinstance(value, list):
    raise TypeError(f"Snapper setup {label} must be a list")
  groups: list[list[str]] = []
  for index, command in enumerate(value):
    groups.append(_text_list(command, f"{label}[{index}]"))
  return groups


def _path_settings(value: object, label: str) -> PathSetting:
  setting = _mapping(value, label)
  return {
    "default": _text(setting.get("default"), f"{label}.default"),
    "environment_override": _text(setting.get("environment_override"), f"{label}.environment_override"),
  }


def _settings() -> Settings:
  ap = Path(os.environ["AP"])
  with (ap / "data/installer/snapper-setup.yml").open(encoding="utf-8") as stream:
    raw: object = yaml.safe_load(stream)
  root = _mapping(raw, "configuration")
  snapper = _mapping(root.get("snapper"), "configuration.snapper")
  paths = _mapping(snapper.get("paths"), "paths")
  test_mode = _mapping(snapper.get("test_mode"), "test_mode")
  commands = _mapping(snapper.get("commands"), "commands")
  return {
    "paths": {
      "config": _path_settings(paths.get("config"), "paths.config"),
      "conf": _path_settings(paths.get("conf"), "paths.conf"),
      "template": _path_settings(paths.get("template"), "paths.template"),
    },
    "directory_mode": _mode(snapper.get("directory_mode"), "directory_mode"),
    "file_mode": _mode(snapper.get("file_mode"), "file_mode"),
    "config_file_contents": _text(snapper.get("config_file_contents"), "config_file_contents"),
    "test_mode": {
      "environment_variable": _text(test_mode.get("environment_variable"), "test_mode.environment_variable"),
      "disabled_value": _text(test_mode.get("disabled_value"), "test_mode.disabled_value"),
      "enabled_value": _text(test_mode.get("enabled_value"), "test_mode.enabled_value"),
    },
    "commands": {
      "create_config_primary": _text_list(commands.get("create_config_primary"), "commands.create_config_primary"),
      "create_config_fallback": _text_list(commands.get("create_config_fallback"), "commands.create_config_fallback"),
      "disable_timeline": _command_groups(commands.get("disable_timeline"), "commands.disable_timeline"),
      "enable_cleanup": _command_groups(commands.get("enable_cleanup"), "commands.enable_cleanup"),
      "disable_legacy_snapshot_sync": _command_groups(
        commands.get("disable_legacy_snapshot_sync"),
        "commands.disable_legacy_snapshot_sync",
      ),
    },
  }


def _path(settings: Settings, key: Literal["config", "conf", "template"]) -> Path:
  value = settings["paths"][key]
  override = os.environ.get(value["environment_override"])
  if override is not None and override != "":
    return Path(override)
  if key == "template":
    return Path(os.environ["AP"]) / value["default"]
  return Path(value["default"])


def _atomic_write(path: Path, content: bytes, mode: int, directory_mode: str) -> None:
  path.parent.mkdir(mode=int(directory_mode, 8), parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as stream:
      stream.write(content)
      stream.flush()
      os.fsync(stream.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def _create_config_if_missing(config_path: Path, settings: Settings) -> None:
  if config_path.is_file():
    return
  config_path.parent.mkdir(mode=int(settings["directory_mode"], 8), parents=True, exist_ok=True)
  test = settings["test_mode"]
  if os.environ.get(test["environment_variable"], test["disabled_value"]) == test["enabled_value"]:
    _atomic_write(config_path, b"", int(settings["file_mode"], 8), settings["directory_mode"])
    return

  primary = subprocess.run(settings["commands"]["create_config_primary"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  if primary.returncode:
    subprocess.run(settings["commands"]["create_config_fallback"], check=True, stdout=subprocess.DEVNULL)


def _run_optional(commands: list[list[str]]) -> None:
  for command in commands:
    subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
  settings = _settings()
  config_path = _path(settings, "config")
  conf_path = _path(settings, "conf")
  template_path = _path(settings, "template")
  _create_config_if_missing(config_path, settings)
  _atomic_write(config_path, template_path.read_bytes(), int(settings["file_mode"], 8), settings["directory_mode"])
  _atomic_write(conf_path, settings["config_file_contents"].encode(), int(settings["file_mode"], 8), settings["directory_mode"])
  _run_optional(settings["commands"]["disable_timeline"])
  _run_optional(settings["commands"]["enable_cleanup"])
  _run_optional(settings["commands"]["disable_legacy_snapshot_sync"])
  return 0


if __name__ == "__main__":
  try:
    raise SystemExit(main())
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load or apply Snapper setup configuration: {error}", file=sys.stderr)
    raise SystemExit(os.EX_CONFIG) from error
  except (subprocess.SubprocessError, RuntimeError) as error:
    print(f"Could not apply Snapper setup: {error}", file=sys.stderr)
    raise SystemExit(os.EX_SOFTWARE) from error
