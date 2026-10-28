#!/usr/bin/python3
"""Maintain systemd-boot entries for root filesystem snapshots."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import TypedDict, TypeGuard
import xml.etree.ElementTree as ET

import yaml


class EnvironmentDefault(TypedDict):
  environment: str
  default: str


class MachineIdPath(TypedDict):
  environment: str
  source: str


class PathSettings(TypedDict):
  machine_id_pattern: str
  boot_root: EnvironmentDefault
  snapshots_root: EnvironmentDefault
  machine_id: MachineIdPath
  uki: EnvironmentDefault
  systemd_unit_dir: EnvironmentDefault
  systemd_libexec_dir: EnvironmentDefault
  limine_snapper_plugin: EnvironmentDefault
  image_directory: str
  entries_directory: str
  converter_files: list[str]


class SnapshotSettings(TypedDict):
  root_subvolume: str
  id_pattern: str
  actions: dict[str, str]
  argument_positions: dict[str, int]
  directory: str
  info_file: str
  archive_file: str
  entry_file: str


class BootSettings(TypedDict):
  product_pattern: str
  legacy_disable_command: list[str]
  converter_disable_command: list[str]
  reload_command: list[str]
  trusted_path: str
  objcopy_command: list[str]
  status_command: list[str]
  cmdline_section: str
  snapshot_rootflag: str
  entry_title: str
  entry_sort_key: str
  entry_uki_path: str
  legacy_entry_files: list[str]
  entry_template: str


class SnapperSettings(TypedDict):
  paths: PathSettings
  snapshot: SnapshotSettings
  boot: BootSettings
  limits: dict[str, int]
  modes: dict[str, str]
  messages: dict[str, dict[str, str]]


class RuntimePaths(TypedDict):
  boot_root: str
  snapshots_root: str
  systemd_unit_dir: str
  systemd_libexec_dir: str
  limine_snapper_plugin: str
  machine_id: str
  uki: str
  image_directory: str
  entries_directory: str


def _is_string_mapping(value: object) -> TypeGuard[dict[str, str]]:
  return isinstance(value, dict) and all(
    isinstance(key, str) and isinstance(item, str) for key, item in value.items()
  )


def _is_string_list(value: object) -> TypeGuard[list[str]]:
  return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_integer_mapping(value: object, required: set[str]) -> TypeGuard[dict[str, int]]:
  return (
    isinstance(value, dict)
    and required.issubset(value)
    and all(isinstance(key, str) and type(item) is int for key, item in value.items())
  )


def _is_snapper_settings(value: object) -> TypeGuard[SnapperSettings]:
  if not isinstance(value, dict):
    return False
  paths = value.get("paths")
  snapshot = value.get("snapshot")
  boot = value.get("boot")
  limits = value.get("limits")
  modes = value.get("modes")
  messages = value.get("messages")
  if not all(isinstance(section, dict) for section in (paths, snapshot, boot, limits, modes, messages)):
    return False
  if not isinstance(paths, dict) or not isinstance(snapshot, dict) or not isinstance(boot, dict):
    return False
  path_names = (
    "boot_root", "snapshots_root", "uki", "systemd_unit_dir", "systemd_libexec_dir",
    "limine_snapper_plugin",
  )
  if (
    not isinstance(paths.get("machine_id_pattern"), str)
    or any(
      not isinstance(paths.get(name), dict)
      or not isinstance(paths[name].get("environment"), str)
      or not isinstance(paths[name].get("default"), str)
      for name in path_names
    )
    or not isinstance(paths.get("machine_id"), dict)
    or not isinstance(paths["machine_id"].get("environment"), str)
    or not isinstance(paths["machine_id"].get("source"), str)
    or not isinstance(paths.get("image_directory"), str)
    or not isinstance(paths.get("entries_directory"), str)
    or not _is_string_list(paths.get("converter_files"))
  ):
    return False
  snapshot_strings = (
    "root_subvolume", "id_pattern", "directory", "info_file", "archive_file", "entry_file",
  )
  if (
    any(not isinstance(snapshot.get(key), str) for key in snapshot_strings)
    or not _is_string_mapping(snapshot.get("actions"))
    or not {"create", "delete"}.issubset(snapshot["actions"])
    or not _is_integer_mapping(snapshot.get("argument_positions"), {"action", "subvolume", "snapshot_id"})
  ):
    return False
  boot_commands = (
    "legacy_disable_command", "converter_disable_command", "reload_command", "objcopy_command", "status_command",
  )
  boot_strings = (
    "product_pattern", "trusted_path", "cmdline_section", "snapshot_rootflag", "entry_title",
    "entry_sort_key", "entry_uki_path", "entry_template",
  )
  if (
    any(not _is_string_list(boot.get(key)) for key in boot_commands)
    or any(not isinstance(boot.get(key), str) for key in boot_strings)
    or not _is_string_list(boot.get("legacy_entry_files"))
    or not _is_integer_mapping(limits, {"snapshot_info_bytes"})
    or not _is_string_mapping(modes)
    or "installed_file" not in modes
    or not isinstance(messages, dict)
    or not all(isinstance(language, str) and _is_string_mapping(entries) for language, entries in messages.items())
    or not isinstance(messages.get("en"), dict)
  ):
    return False
  return True


def message(settings: SnapperSettings, key: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = settings.get("messages", {})
  return messages.get(language, messages["en"])[key]


def load_settings() -> SnapperSettings:
  if os.geteuid() == 0:
    path = Path(__file__).with_suffix(".yml")
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
      metadata = os.fstat(stream.fileno())
      if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0 or stat.S_IMODE(metadata.st_mode) & 0o022:
        raise PermissionError("systemd-boot Snapper settings must be a root-owned, non-writable regular file")
      settings: object = yaml.safe_load(stream)
  else:
    ap = Path(os.environ["ARCH_PATH"])
    path = ap / "data/installer/systemd-boot-snapper-plugin.yml"
    settings = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not _is_snapper_settings(settings):
    raise ValueError("Invalid systemd-boot Snapper plugin settings")
  return settings


def runtime_paths(settings: SnapperSettings) -> tuple[RuntimePaths, list[str]]:
  paths = settings["paths"]
  allow_environment = os.geteuid() != 0
  values: RuntimePaths = {
    "boot_root": "",
    "snapshots_root": "",
    "systemd_unit_dir": "",
    "systemd_libexec_dir": "",
    "limine_snapper_plugin": "",
    "machine_id": "",
    "uki": "",
    "image_directory": "",
    "entries_directory": "",
  }
  for name in ("boot_root", "snapshots_root", "systemd_unit_dir", "systemd_libexec_dir", "limine_snapper_plugin"):
    item = paths[name]
    environment_value = os.environ.get(item["environment"]) if allow_environment else None
    values[name] = environment_value or item["default"]

  machine_item = paths["machine_id"]
  machine_environment = os.environ.get(machine_item["environment"]) if allow_environment else None
  machine_id = machine_environment or Path(machine_item["source"]).read_text(encoding="utf-8").strip()
  if re.fullmatch(paths["machine_id_pattern"], machine_id) is None:
    raise ValueError(message(settings, "invalid_machine_id"))
  values["machine_id"] = machine_id

  uki_item = paths["uki"]
  environment_uki = os.environ.get(uki_item["environment"]) if allow_environment else None
  values["uki"] = environment_uki or uki_item["default"].format(boot_root=values["boot_root"])
  values["image_directory"] = paths["image_directory"].format(**values)
  values["entries_directory"] = paths["entries_directory"].format(**values)
  converter_files = [value.format(**values) for value in paths["converter_files"]]
  return values, converter_files


def configured_path(template: str, paths: RuntimePaths, snapshot_id: str) -> Path:
  return Path(template.format(**paths, snapshot_id=snapshot_id))


def run_quietly(command: list[str]) -> None:
  subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_legacy_converter(settings: SnapperSettings, paths: RuntimePaths, converter_files: list[str]) -> None:
  boot = settings["boot"]
  run_quietly(boot["legacy_disable_command"])
  legacy_plugin = Path(paths["limine_snapper_plugin"])
  try:
    mode = legacy_plugin.lstat().st_mode
  except FileNotFoundError:
    pass
  else:
    if stat.S_ISREG(mode):
      legacy_plugin.chmod(stat.S_IMODE(mode) & ~0o111, follow_symlinks=False)
  run_quietly(boot["converter_disable_command"])
  for value in converter_files:
    path = Path(value)
    if path.is_file() or path.is_symlink():
      path.unlink()
  subprocess.run(boot["reload_command"], check=True, stdout=subprocess.DEVNULL)


def systemd_boot_is_active(settings: SnapperSettings) -> bool:
  result = subprocess.run(
    settings["boot"]["status_command"], check=False, capture_output=True, text=True,
  )
  if result.returncode:
    return False
  return re.search(settings["boot"]["product_pattern"], result.stdout, re.MULTILINE) is not None


def snapshot_date(info_file: Path, maximum_bytes: int) -> str:
  try:
    if info_file.is_symlink() or not info_file.is_file() or info_file.stat().st_size > maximum_bytes:
      return ""
    root = ET.fromstring(info_file.read_bytes())
    stamp = root.findtext("date", "")
    parsed = datetime.datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
    return parsed.strftime("%Y-%m-%d %H:%M:%S")
  except (OSError, ValueError, ET.ParseError):
    return ""


def snapshot_cmdline(uki: Path, snapshot_id: str, settings: SnapperSettings, directory: Path) -> Path:
  command = settings["boot"]["objcopy_command"]
  section = settings["boot"]["cmdline_section"]
  descriptor, name = tempfile.mkstemp(prefix=".arch-snapshot-cmdline.")
  os.close(descriptor)
  cmdline = Path(name)
  try:
    subprocess.run([*command, "-O", "binary", f"--only-section={section}", str(uki), str(cmdline)], check=True)
    tokens = cmdline.read_bytes().rstrip(b"\0\n ").decode("utf-8").split()
    for index, token in enumerate(tokens):
      if token.startswith("rootflags="):
        flags = token.removeprefix("rootflags=").split(",")
        flags = [flag for flag in flags if not flag.startswith(("subvol=", "subvolid="))]
        replacement = settings["boot"]["snapshot_rootflag"].format(snapshot_id=snapshot_id)
        tokens[index] = "rootflags=" + ",".join([replacement, *flags])
        break
    else:
      raise ValueError(message(settings, "missing_rootflags"))
    cmdline.write_bytes((" ".join(tokens) + "\0").encode("utf-8"))
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".snapshot-{snapshot_id}.", suffix=".efi", dir=directory)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
      if uki.is_symlink() or not uki.is_file():
        raise ValueError(message(settings, "invalid_uki"))
      shutil.copyfile(uki, temporary, follow_symlinks=False)
      subprocess.run([*command, f"--update-section", f"{section}={cmdline}", str(temporary)], check=True)
      temporary.chmod(int(settings["modes"]["installed_file"], 8))
      return temporary
    except BaseException:
      temporary.unlink(missing_ok=True)
      raise
  finally:
    cmdline.unlink(missing_ok=True)


def write_entry(path: Path, content: str, mode: str) -> None:
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
      stream.write(content)
      stream.flush()
      os.fsync(stream.fileno())
    temporary.chmod(int(mode, 8))
    os.replace(temporary, path)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def create_snapshot(snapshot_id: str, settings: SnapperSettings, paths: RuntimePaths) -> None:
  snapshot = settings["snapshot"]
  boot = settings["boot"]
  snapshot_dir = configured_path(snapshot["directory"], paths, snapshot_id)
  uki = Path(paths["uki"])
  if not snapshot_dir.is_dir() or uki.is_symlink() or not uki.is_file() or uki.stat().st_size == 0:
    return

  image_directory = Path(paths["image_directory"])
  entries_directory = Path(paths["entries_directory"])
  image_directory.mkdir(parents=True, exist_ok=True)
  entries_directory.mkdir(parents=True, exist_ok=True)
  archive = configured_path(snapshot["archive_file"], paths, snapshot_id)
  entry = configured_path(snapshot["entry_file"], paths, snapshot_id)
  temporary = snapshot_cmdline(uki, snapshot_id, settings, image_directory)
  try:
    os.replace(temporary, archive)
  finally:
    temporary.unlink(missing_ok=True)

  info_file = configured_path(snapshot["info_file"], paths, snapshot_id)
  date = snapshot_date(info_file, settings["limits"]["snapshot_info_bytes"])
  suffix = f" ({date})" if date else ""
  title = boot["entry_title"].format(snapshot_id=snapshot_id, date_suffix=suffix)
  entry_content = boot["entry_template"].format(
    title=title,
    sort_key=boot["entry_sort_key"],
    uki_path=boot["entry_uki_path"].format(machine_id=paths["machine_id"], snapshot_id=snapshot_id),
  ) + "\n"
  write_entry(entry, entry_content, settings["modes"]["installed_file"])
  for template in boot["legacy_entry_files"]:
    configured_path(template, paths, snapshot_id).unlink(missing_ok=True)


def delete_snapshot(snapshot_id: str, settings: SnapperSettings, paths: RuntimePaths) -> None:
  snapshot = settings["snapshot"]
  boot = settings["boot"]
  targets = [
    configured_path(snapshot["archive_file"], paths, snapshot_id),
    configured_path(snapshot["entry_file"], paths, snapshot_id),
    *(configured_path(template, paths, snapshot_id) for template in boot["legacy_entry_files"]),
  ]
  for path in targets:
    path.unlink(missing_ok=True)


def main(arguments: list[str] | None = None) -> int:
  arguments = sys.argv[1:] if arguments is None else arguments
  settings = load_settings()
  if os.geteuid() == 0:
    os.environ["PATH"] = settings["boot"]["trusted_path"]
  positions = settings["snapshot"]["argument_positions"]
  if len(arguments) <= max(positions.values()):
    return 0
  action = arguments[positions["action"]]
  subvolume = arguments[positions["subvolume"]]
  snapshot_id = arguments[positions["snapshot_id"]]
  snapshot = settings["snapshot"]
  if subvolume != snapshot["root_subvolume"] or re.fullmatch(snapshot["id_pattern"], snapshot_id) is None:
    return 0
  if action not in snapshot["actions"].values() or not systemd_boot_is_active(settings):
    return 0

  paths, converter_files = runtime_paths(settings)
  stop_legacy_converter(settings, paths, converter_files)
  if action == snapshot["actions"]["create"]:
    create_snapshot(snapshot_id, settings, paths)
  elif action == snapshot["actions"]["delete"]:
    delete_snapshot(snapshot_id, settings, paths)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
