from __future__ import annotations

import glob
import os
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Paths(TypedDict):
  usb_root_default: str
  usb_root_environment: str
  usb_device_glob: str
  product_file: str
  vendor_file: str
  interface_glob: str
  driver_link: str
  platform_manifest_default: str
  platform_manifest_environment: str
  encoding: str


class Identifiers(TypedDict):
  platform_manifest_fields: int
  ignored_kernel_driver: str
  product_substrings: list[str]
  product_prefixes: list[str]
  usb_vendor_ids: list[str]


class Limits(TypedDict):
  manifest_bytes: int
  attribute_bytes: int
  platform_matches: int
  usb_devices: int
  usb_interfaces: int


class Statuses(TypedDict):
  detected: int
  not_detected: int
  configuration_error: int


class Messages(TypedDict):
  detection_failed: str


class Settings(TypedDict):
  paths: Paths
  identifiers: Identifiers
  limits: Limits
  statuses: Statuses
  messages: Messages


def _mapping(value: object) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError()
  return cast(dict[str, object], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError()
  return value


def _text_list(value: object) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError()
  return cast(list[str], value)


def _positive_integer(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
    raise ValueError()
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw = yaml.safe_load((root / "data/cli/hardware-fingerprint.yml").read_text(encoding="utf-8"))
  document = _mapping(raw)
  raw_paths = _mapping(document.get("paths"))
  raw_identifiers = _mapping(document.get("identifiers"))
  raw_limits = _mapping(document.get("limits"))
  raw_statuses = _mapping(document.get("statuses"))
  raw_messages = _mapping(document.get("messages"))
  paths: Paths = {
    "usb_root_default": _text(raw_paths.get("usb_root_default")),
    "usb_root_environment": _text(raw_paths.get("usb_root_environment")),
    "usb_device_glob": _text(raw_paths.get("usb_device_glob")),
    "product_file": _text(raw_paths.get("product_file")),
    "vendor_file": _text(raw_paths.get("vendor_file")),
    "interface_glob": _text(raw_paths.get("interface_glob")),
    "driver_link": _text(raw_paths.get("driver_link")),
    "platform_manifest_default": _text(raw_paths.get("platform_manifest_default")),
    "platform_manifest_environment": _text(raw_paths.get("platform_manifest_environment")),
    "encoding": _text(raw_paths.get("encoding")),
  }
  identifiers: Identifiers = {
    "platform_manifest_fields": _positive_integer(raw_identifiers.get("platform_manifest_fields")),
    "ignored_kernel_driver": _text(raw_identifiers.get("ignored_kernel_driver")),
    "product_substrings": _text_list(raw_identifiers.get("product_substrings")),
    "product_prefixes": _text_list(raw_identifiers.get("product_prefixes")),
    "usb_vendor_ids": _text_list(raw_identifiers.get("usb_vendor_ids")),
  }
  limits: Limits = {
    "manifest_bytes": _positive_integer(raw_limits.get("manifest_bytes")),
    "attribute_bytes": _positive_integer(raw_limits.get("attribute_bytes")),
    "platform_matches": _positive_integer(raw_limits.get("platform_matches")),
    "usb_devices": _positive_integer(raw_limits.get("usb_devices")),
    "usb_interfaces": _positive_integer(raw_limits.get("usb_interfaces")),
  }
  statuses: Statuses = {
    "detected": _positive_or_zero(raw_statuses.get("detected")),
    "not_detected": _positive_or_zero(raw_statuses.get("not_detected")),
    "configuration_error": _positive_integer(raw_statuses.get("configuration_error")),
  }
  messages: Messages = {
    "detection_failed": _text(raw_messages.get("detection_failed")),
  }
  if len(set(statuses.values())) != len(statuses):
    raise ValueError()
  return {"paths": paths, "identifiers": identifiers, "limits": limits, "statuses": statuses, "messages": messages}


def _positive_or_zero(value: object) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError()
  return value


def _read_value(path: Path, settings: Settings) -> str | None:
  try:
    with path.open(encoding=settings["paths"]["encoding"]) as stream:
      value = stream.read(settings["limits"]["attribute_bytes"] + 1)
  except (OSError, UnicodeError):
    return None
  if len(value) > settings["limits"]["attribute_bytes"]:
    return None
  return value.rstrip("\n")


def _platform_reader_present(settings: Settings) -> bool:
  paths = settings["paths"]
  manifest = Path(os.environ.get(paths["platform_manifest_environment"], paths["platform_manifest_default"]))
  try:
    with manifest.open(encoding=paths["encoding"], errors="replace") as stream:
      contents = stream.read(settings["limits"]["manifest_bytes"] + 1)
  except OSError:
    return False
  if len(contents.encode(paths["encoding"], errors="replace")) > settings["limits"]["manifest_bytes"]:
    return False

  expected_fields = settings["identifiers"]["platform_manifest_fields"]
  match_limit = settings["limits"]["platform_matches"]
  for line in contents.splitlines():
    fields = line.split()
    if len(fields) != expected_fields:
      continue
    pattern, expected = fields
    if not Path(pattern).is_absolute():
      continue
    for index, match in enumerate(glob.iglob(pattern)):
      if index >= match_limit:
        break
      if _read_value(Path(match), settings) == expected:
        return True
  return False


def _has_kernel_driver(device: Path, settings: Settings) -> bool:
  paths = settings["paths"]
  limits = settings["limits"]
  ignored_driver = settings["identifiers"]["ignored_kernel_driver"]
  for index, interface in enumerate(device.glob(paths["interface_glob"])):
    if index >= limits["usb_interfaces"]:
      return True
    driver = interface / paths["driver_link"]
    if not driver.exists():
      continue
    try:
      driver_name = driver.resolve(strict=True).name
    except (OSError, RuntimeError):
      return True
    if driver_name != ignored_driver:
      return True
  return False


def _usb_reader_present(settings: Settings) -> bool:
  paths = settings["paths"]
  identifiers = settings["identifiers"]
  root = Path(os.environ.get(paths["usb_root_environment"], paths["usb_root_default"]))
  for index, device in enumerate(root.glob(paths["usb_device_glob"])):
    if index >= settings["limits"]["usb_devices"]:
      return False
    product = _read_value(device / paths["product_file"], settings)
    if product is not None:
      normalized = product.lower()
      if any(value in normalized for value in identifiers["product_substrings"]):
        return True
      if any(normalized.startswith(value) for value in identifiers["product_prefixes"]):
        return True

    vendor = _read_value(device / paths["vendor_file"], settings)
    if vendor in identifiers["usb_vendor_ids"] and not _has_kernel_driver(device, settings):
      return True
  return False


def fingerprint_main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return os.EX_CONFIG
  try:
    detected = _platform_reader_present(settings) or _usb_reader_present(settings)
    return settings["statuses"]["detected"] if detected else settings["statuses"]["not_detected"]
  except (OSError, TypeError, UnicodeError, ValueError):
    print(settings["messages"]["detection_failed"], file=sys.stderr)
    return settings["statuses"]["configuration_error"]
