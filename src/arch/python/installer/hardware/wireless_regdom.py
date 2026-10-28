from __future__ import annotations

import fcntl
import errno
import os
import re
import stat
from pathlib import Path
from typing import TypedDict, TypeGuard

import yaml


class WirelessRegdomSettings(TypedDict):
  root_environment: str
  regdom_file: str
  existing_setting_pattern: str
  zoneinfo_directory: str
  localtime_file: str
  country_pattern: str
  zone_table: str
  zone_table_country_column: int
  zone_table_timezone_column: int
  line_template: str


def _is_wireless_regdom_settings(value: object) -> TypeGuard[WirelessRegdomSettings]:
  if not isinstance(value, dict):
    return False
  text_fields = (
    "root_environment", "regdom_file", "existing_setting_pattern", "zoneinfo_directory", "localtime_file",
    "country_pattern", "zone_table", "line_template",
  )
  return (
    all(isinstance(value.get(key), str) for key in text_fields)
    and type(value.get("zone_table_country_column")) is int
    and type(value.get("zone_table_timezone_column")) is int
  )


def _timezone_country(root: Path, settings: WirelessRegdomSettings) -> str:
  zoneinfo = root / settings["zoneinfo_directory"]
  localtime = root / settings["localtime_file"]
  try:
    timezone_path = localtime.resolve(strict=True)
    timezone = timezone_path.relative_to(zoneinfo.resolve(strict=True)).as_posix()
  except (OSError, ValueError):
    return ""

  country = timezone.split("/", 1)[0]
  if re.fullmatch(settings["country_pattern"], country):
    return country

  table = root / str(settings["zone_table"])
  try:
    lines = table.read_text(encoding="utf-8").splitlines()
  except OSError:
    return ""
  country_column = settings["zone_table_country_column"]
  timezone_column = settings["zone_table_timezone_column"]
  for line in lines:
    if not line or line.startswith("#"):
      continue
    columns = line.split()
    if len(columns) > max(country_column, timezone_column) and columns[timezone_column] == timezone:
      candidate = columns[country_column]
      if re.fullmatch(settings["country_pattern"], candidate):
        return candidate
      return ""
  return ""


def _append_unset(path: Path, setting_pattern: str, line: str) -> None:
  target = path.resolve(strict=True)
  flags = os.O_RDWR | os.O_APPEND | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
  descriptor = os.open(target, flags)
  try:
    fcntl.flock(descriptor, fcntl.LOCK_EX)
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
      return
    content = os.pread(descriptor, metadata.st_size, 0).decode("utf-8")
    if re.search(setting_pattern, content, flags=re.MULTILINE):
      return
    suffix = "" if not content or content.endswith("\n") else "\n"
    addition = f"{suffix}{line}\n".encode("utf-8")
    remaining = memoryview(addition)
    while remaining:
      written = os.write(descriptor, remaining)
      if written <= 0:
        raise OSError(errno.EIO, os.strerror(errno.EIO))
      remaining = remaining[written:]
    os.fsync(descriptor)
  finally:
    os.close(descriptor)


def main() -> int:
  root_path = os.environ["AP"]
  config: object = yaml.safe_load((Path(root_path) / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid hardware setup configuration")
  settings = config["wireless_regdom"]
  if not _is_wireless_regdom_settings(settings):
    raise ValueError("invalid wireless regulatory domain configuration")
  system_root = Path(os.environ.get(settings["root_environment"]) or "/").resolve()
  config_file = system_root / str(settings["regdom_file"])
  if not config_file.is_file():
    return 0
  try:
    if re.search(settings["existing_setting_pattern"], config_file.read_text(encoding="utf-8"), flags=re.MULTILINE):
      return 0
  except OSError:
    return 0

  country = _timezone_country(system_root, settings)
  if country:
    line = str(settings["line_template"]).format(country=country)
    _append_unset(config_file, settings["existing_setting_pattern"], line)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
