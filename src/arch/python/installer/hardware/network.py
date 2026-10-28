from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TypedDict, TypeGuard

import yaml


class NetworkSettings(TypedDict):
  systemctl_command: list[str]
  disable_units: list[str]
  mask_units: list[str]
  network_directory: str
  timestamp_format: str
  backup_directory_template: str
  network_files: list[str]
  dhcp_pattern: str
  interface_pattern: str
  manager_active_command: list[str]
  stop_command: list[str]


def _string_list(value: object) -> TypeGuard[list[str]]:
  return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _network_settings(value: object) -> TypeGuard[NetworkSettings]:
  if not isinstance(value, dict):
    return False
  return (
    _string_list(value.get("systemctl_command"))
    and _string_list(value.get("disable_units"))
    and _string_list(value.get("mask_units"))
    and isinstance(value.get("network_directory"), str)
    and isinstance(value.get("timestamp_format"), str)
    and isinstance(value.get("backup_directory_template"), str)
    and _string_list(value.get("network_files"))
    and isinstance(value.get("dhcp_pattern"), str)
    and isinstance(value.get("interface_pattern"), str)
    and _string_list(value.get("manager_active_command"))
    and _string_list(value.get("stop_command"))
  )


def _run(command: list[str]) -> int | None:
  try:
    return subprocess.run(command, check=False, stderr=subprocess.DEVNULL).returncode
  except OSError:
    return None


def _is_stock_networkd_file(path: Path, settings: NetworkSettings) -> bool:
  if not path.is_file() or path.name not in settings["network_files"]:
    return False
  try:
    content = path.read_text(encoding="utf-8", errors="replace")
  except OSError:
    return False
  return (
    re.search(settings["dhcp_pattern"], content, flags=re.MULTILINE) is not None
    and re.search(settings["interface_pattern"], content, flags=re.MULTILINE) is not None
  )


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config: object = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid hardware setup configuration")
  settings = config["network_setup"]
  if not _network_settings(settings):
    raise ValueError("invalid network setup configuration")
  systemctl = settings["systemctl_command"]

  for unit in settings["disable_units"]:
    _run([*systemctl, "disable", unit])
  for unit in settings["mask_units"]:
    _run([*systemctl, "mask", unit])

  network_directory = Path(settings["network_directory"])
  timestamp = datetime.now().astimezone().strftime(settings["timestamp_format"])
  backup_directory = network_directory / settings["backup_directory_template"].format(timestamp=timestamp)
  for filename in settings["network_files"]:
    source = network_directory / filename
    if _is_stock_networkd_file(source, settings):
      backup_directory.mkdir(mode=stat.S_IRWXU, parents=True, exist_ok=True)
      backup_directory.chmod(stat.S_IRWXU)
      shutil.move(str(source), str(backup_directory))

  manager_active = _run(settings["manager_active_command"])
  if manager_active == 0:
    _run([*settings["stop_command"]])
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
