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
import xml.etree.ElementTree as ET

import yaml


def message(settings: dict, key: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = settings.get("messages", {})
  return messages.get(language, messages["en"])[key]


def load_settings() -> dict:
  if os.geteuid() == 0:
    path = Path(__file__).with_suffix(".yml")
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
      metadata = os.fstat(stream.fileno())
      if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0 or stat.S_IMODE(metadata.st_mode) & 0o022:
        raise PermissionError("systemd-boot Snapper settings must be a root-owned, non-writable regular file")
      settings = yaml.safe_load(stream)
  else:
    arch_path = Path(os.environ["ARCH_PATH"])
    path = arch_path / "data/installer/systemd-boot-snapper-plugin.yml"
    settings = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("Invalid systemd-boot Snapper plugin settings")
  return settings


def runtime_paths(settings: dict) -> dict[str, str]:
  paths = settings["paths"]
  allow_environment = os.geteuid() != 0
  values: dict[str, str] = {}
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
  values["converter_files"] = [value.format(**values) for value in paths["converter_files"]]
  return values


def configured_path(template: str, paths: dict[str, str], snapshot_id: str) -> Path:
  return Path(template.format(**paths, snapshot_id=snapshot_id))


def run_quietly(command: list[str]) -> None:
  subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_legacy_converter(settings: dict, paths: dict[str, str]) -> None:
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
  for value in paths["converter_files"]:
    path = Path(value)
    if path.is_file() or path.is_symlink():
      path.unlink()
  subprocess.run(boot["reload_command"], check=True, stdout=subprocess.DEVNULL)


def systemd_boot_is_active(settings: dict) -> bool:
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


def snapshot_cmdline(uki: Path, snapshot_id: str, settings: dict, directory: Path) -> Path:
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


def create_snapshot(snapshot_id: str, settings: dict, paths: dict[str, str]) -> None:
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


def delete_snapshot(snapshot_id: str, settings: dict, paths: dict[str, str]) -> None:
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

  paths = runtime_paths(settings)
  stop_legacy_converter(settings, paths)
  if action == snapshot["actions"]["create"]:
    create_snapshot(snapshot_id, settings, paths)
  elif action == snapshot["actions"]["delete"]:
    delete_snapshot(snapshot_id, settings, paths)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
