from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import NotRequired, TypedDict

import yaml


class BackupDirectory(TypedDict):
  parent: str
  name: str
  timestamp_format: str


class FileEntry(TypedDict):
  source: str
  target: NotRequired[str]
  target_environment: NotRequired[str]
  target_default: NotRequired[str]
  target_name: NotRequired[str]


class TreeEntry(TypedDict):
  source: str
  target: str


class Plymouth(TypedDict):
  config: str
  expected_line: str
  command: list[str]


class BootName(TypedDict):
  match: str
  replacement: str


class Settings(TypedDict):
  backup_directory: BackupDirectory
  files: list[FileEntry]
  trees: list[TreeEntry]
  tree_files: list[TreeEntry]
  skeleton_files: list[TreeEntry]
  plymouth: Plymouth
  boot_configs: list[str]
  boot_name: BootName
  installed_file_mode: str


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid branding setup settings: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid branding setup settings: {label} must be a string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list):
    raise TypeError(f"invalid branding setup settings: {label} must be a list")
  return [_text(item, f"{label} item") for item in value]


def _entries(value: object, label: str) -> list[FileEntry]:
  if not isinstance(value, list):
    raise TypeError(f"invalid branding setup settings: {label} must be a list")
  entries: list[FileEntry] = []
  for index, raw_entry in enumerate(value):
    entry = _mapping(raw_entry, f"{label}[{index}]")
    parsed: FileEntry = {"source": _text(entry.get("source"), f"{label}[{index}].source")}
    if "target" in entry:
      parsed["target"] = _text(entry.get("target"), f"{label}[{index}].target")
    if "target_environment" in entry:
      parsed["target_environment"] = _text(entry.get("target_environment"), f"{label}[{index}].target_environment")
      parsed["target_default"] = _text(entry.get("target_default"), f"{label}[{index}].target_default")
      parsed["target_name"] = _text(entry.get("target_name"), f"{label}[{index}].target_name")
    if "target" not in parsed and "target_environment" not in parsed:
      raise ValueError(f"invalid branding setup settings: {label}[{index}] has no target")
    entries.append(parsed)
  return entries


def _tree_entries(value: object, label: str) -> list[TreeEntry]:
  if not isinstance(value, list):
    raise TypeError(f"invalid branding setup settings: {label} must be a list")
  entries: list[TreeEntry] = []
  for index, raw_entry in enumerate(value):
    entry = _mapping(raw_entry, f"{label}[{index}]")
    entries.append({
      "source": _text(entry.get("source"), f"{label}[{index}].source"),
      "target": _text(entry.get("target"), f"{label}[{index}].target"),
    })
  return entries


def _settings() -> tuple[Path, Settings]:
  ap = Path(os.environ["AP"])
  with (ap / "data/installer/branding-setup.yml").open(encoding="utf-8") as stream:
    raw: object = yaml.safe_load(stream)
  root = _mapping(raw, "configuration")
  settings = _mapping(root.get("branding"), "branding")
  backup = _mapping(settings.get("backup_directory"), "backup_directory")
  plymouth = _mapping(settings.get("plymouth"), "plymouth")
  boot_name = _mapping(settings.get("boot_name"), "boot_name")
  return ap, {
    "backup_directory": {
      "parent": _text(backup.get("parent"), "backup_directory.parent"),
      "name": _text(backup.get("name"), "backup_directory.name"),
      "timestamp_format": _text(backup.get("timestamp_format"), "backup_directory.timestamp_format"),
    },
    "files": _entries(settings.get("files"), "files"),
    "trees": _tree_entries(settings.get("trees"), "trees"),
    "tree_files": _tree_entries(settings.get("tree_files"), "tree_files"),
    "skeleton_files": _tree_entries(settings.get("skeleton_files"), "skeleton_files"),
    "plymouth": {
      "config": _text(plymouth.get("config"), "plymouth.config"),
      "expected_line": _text(plymouth.get("expected_line"), "plymouth.expected_line"),
      "command": _text_list(plymouth.get("command"), "plymouth.command"),
    },
    "boot_configs": _text_list(settings.get("boot_configs"), "boot_configs"),
    "boot_name": {
      "match": _text(boot_name.get("match"), "boot_name.match"),
      "replacement": _text(boot_name.get("replacement"), "boot_name.replacement"),
    },
    "installed_file_mode": _text(settings.get("installed_file_mode"), "installed_file_mode"),
  }


def _backup_directory(settings: Settings) -> Path:
  backup = settings["backup_directory"]
  timestamp = datetime.now().astimezone().strftime(backup["timestamp_format"])
  return Path(backup["parent"]) / f'{backup["name"]}-{timestamp}'


def _backup(path: Path, backup_dir: Path) -> None:
  destination = backup_dir / path.relative_to(path.anchor)
  destination.parent.mkdir(parents=True, exist_ok=True)
  if path.is_symlink():
    destination.symlink_to(os.readlink(path))
  elif path.is_dir():
    shutil.copytree(path, destination, symlinks=True, dirs_exist_ok=True)
  else:
    shutil.copy2(path, destination, follow_symlinks=False)


def _replace_file(source: Path, target: Path, mode: int, backup_dir: Path) -> None:
  target.parent.mkdir(parents=True, exist_ok=True)
  if target.is_file() and not target.is_symlink() and source.read_bytes() == target.read_bytes():
    return
  if target.exists() or target.is_symlink():
    _backup(target, backup_dir)

  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as output, source.open("rb") as input_stream:
      shutil.copyfileobj(input_stream, output)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, target)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def _target(entry: FileEntry) -> Path:
  if "target_environment" in entry:
    parent = os.environ.get(entry["target_environment"], entry["target_default"])
    return Path(parent) / entry["target_name"]
  return Path(entry["target"])


def main() -> int:
  try:
    ap, settings = _settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load branding setup configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    backup_dir = _backup_directory(settings)
    mode = int(settings["installed_file_mode"], 8)

    for entry in settings["files"]:
      _replace_file(ap / entry["source"], _target(entry), mode, backup_dir)

    for entry in settings["trees"]:
      shutil.copytree(ap / entry["source"], entry["target"], symlinks=True, dirs_exist_ok=True)

    for entry in settings["tree_files"]:
      _replace_file(ap / entry["source"], Path(entry["target"]), mode, backup_dir)

    for entry in settings["skeleton_files"]:
      _replace_file(ap / entry["source"], Path(entry["target"]), mode, backup_dir)

    plymouth = settings["plymouth"]
    if plymouth["expected_line"] not in Path(plymouth["config"]).read_text(encoding="utf-8").splitlines():
      subprocess.run(plymouth["command"], check=True)

    boot_name = settings["boot_name"]
    for value in settings["boot_configs"]:
      path = Path(value)
      if not path.is_file():
        continue
      original = path.read_text(encoding="utf-8")
      if boot_name["match"] not in original:
        continue
      _backup(path, backup_dir)
      updated = original.replace(boot_name["match"], boot_name["replacement"])
      descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
      temporary = Path(temporary_name)
      try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
          stream.write(updated)
          stream.flush()
          os.fsync(stream.fileno())
        os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary, path)
      except BaseException:
        temporary.unlink(missing_ok=True)
        raise
  except subprocess.CalledProcessError as error:
    print(f"Branding setup command failed: {error}", file=sys.stderr)
    return error.returncode
  except (OSError, ValueError, subprocess.SubprocessError) as error:
    print(f"Could not apply branding setup: {error}", file=sys.stderr)
    return os.EX_SOFTWARE
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
