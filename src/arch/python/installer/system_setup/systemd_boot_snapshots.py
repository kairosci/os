from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

import yaml


class BootEntry(TypedDict):
  environment_override: str
  default_esp: str
  relative_path: str


class Plugin(TypedDict):
  source: str
  settings_source: str
  settings_suffix: str
  settings_mode: str
  target_environment: str
  target: str
  directory_mode: str
  mode: str


class LegacyPlugin(TypedDict):
  path: str


class Settings(TypedDict):
  helper: str
  boot_entry: BootEntry
  plugin: Plugin
  legacy_plugin: LegacyPlugin
  disable_units: list[str]
  remove_files: list[str]
  reload_units: list[str]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid system setup settings: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid system setup settings: {label} must be a string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list):
    raise TypeError(f"invalid system setup settings: {label} must be a list")
  return [_text(item, f"{label} item") for item in value]


def _mode(value: object, label: str) -> str:
  mode = _text(value, label)
  try:
    parsed = int(mode, 8)
  except ValueError as error:
    raise ValueError(f"invalid system setup settings: {label} must be an octal mode") from error
  if not 0 <= parsed <= 0o7777:
    raise ValueError(f"invalid system setup settings: {label} is outside the supported mode range")
  return mode


def _settings() -> Settings:
  ap = Path(os.environ["AP"])
  with (ap / "data/installer/config-setup.yml").open(encoding="utf-8") as stream:
    raw: object = yaml.safe_load(stream)
  root = _mapping(raw, "configuration")
  snapshots = _mapping(root.get("systemd_boot_snapshots"), "systemd_boot_snapshots")
  boot = _mapping(snapshots.get("boot_entry"), "boot_entry")
  plugin = _mapping(snapshots.get("plugin"), "plugin")
  legacy = _mapping(snapshots.get("legacy_plugin"), "legacy_plugin")
  return {
    "helper": _text(snapshots.get("helper"), "helper"),
    "boot_entry": {
      "environment_override": _text(boot.get("environment_override"), "boot_entry.environment_override"),
      "default_esp": _text(boot.get("default_esp"), "boot_entry.default_esp"),
      "relative_path": _text(boot.get("relative_path"), "boot_entry.relative_path"),
    },
    "plugin": {
      "source": _text(plugin.get("source"), "plugin.source"),
      "settings_source": _text(plugin.get("settings_source"), "plugin.settings_source"),
      "settings_suffix": _text(plugin.get("settings_suffix"), "plugin.settings_suffix"),
      "settings_mode": _mode(plugin.get("settings_mode"), "plugin.settings_mode"),
      "target_environment": _text(plugin.get("target_environment"), "plugin.target_environment"),
      "target": _text(plugin.get("target"), "plugin.target"),
      "directory_mode": _mode(plugin.get("directory_mode"), "plugin.directory_mode"),
      "mode": _mode(plugin.get("mode"), "plugin.mode"),
    },
    "legacy_plugin": {"path": _text(legacy.get("path"), "legacy_plugin.path")},
    "disable_units": _text_list(snapshots.get("disable_units"), "disable_units"),
    "remove_files": _text_list(snapshots.get("remove_files"), "remove_files"),
    "reload_units": _text_list(snapshots.get("reload_units"), "reload_units"),
  }


def _copy_plugin(source: Path, target: Path, mode: str, directory_mode: str) -> None:
  target.parent.mkdir(mode=int(directory_mode, 8), parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as stream, source.open("rb") as plugin:
      shutil.copyfileobj(plugin, stream)
      stream.flush()
      os.fsync(stream.fileno())
    os.chmod(temporary, int(mode, 8))
    os.replace(temporary, target)
    directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def _disable_legacy_plugin(path: Path) -> None:
  try:
    plugin_stat = path.lstat()
  except FileNotFoundError:
    return
  if stat.S_ISREG(plugin_stat.st_mode):
    os.chmod(path, stat.S_IMODE(plugin_stat.st_mode) & ~0o111, follow_symlinks=False)


def _run_optional(command: list[str]) -> None:
  subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load systemd-boot snapshot settings: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    ap = Path(os.environ["AP"])
    helper = subprocess.run([str(ap / settings["helper"])], check=False)
    boot_entry = settings["boot_entry"]
    esp = os.environ.get(boot_entry["environment_override"], boot_entry["default_esp"])
    if helper.returncode or not (Path(esp) / boot_entry["relative_path"]).is_file():
      return 0

    plugin = settings["plugin"]
    target = plugin["target"]
    if os.geteuid() != 0:
      target = os.environ.get(plugin["target_environment"], target)
    _copy_plugin(
      ap / plugin["source"],
      Path(target),
      plugin["mode"],
      plugin["directory_mode"],
    )
    settings_target = Path(target).with_name(Path(target).name + plugin["settings_suffix"])
    _copy_plugin(
      ap / plugin["settings_source"],
      settings_target,
      plugin["settings_mode"],
      plugin["directory_mode"],
    )
    _run_optional(settings["disable_units"])
    _disable_legacy_plugin(Path(settings["legacy_plugin"]["path"]))
    for value in settings["remove_files"]:
      path = Path(value)
      if path.is_file() or path.is_symlink():
        path.unlink()
    subprocess.run(settings["reload_units"], check=True, stdout=subprocess.DEVNULL)
  except subprocess.CalledProcessError as error:
    print(f"Could not reload systemd-boot snapshot setup: {error}", file=sys.stderr)
    return error.returncode
  except (OSError, subprocess.SubprocessError, ValueError) as error:
    print(f"Could not apply systemd-boot snapshot setup: {error}", file=sys.stderr)
    return os.EX_SOFTWARE
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
