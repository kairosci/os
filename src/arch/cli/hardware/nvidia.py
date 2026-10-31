from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Literal, TypedDict

import yaml


class Paths(TypedDict):
  pci_devices: str
  override_environment: str
  device_glob: str
  vendor_attribute: str
  class_attribute: str
  device_attribute: str
  boot_vga_attribute: str
  attribute_encoding: str


class Identifiers(TypedDict):
  vendor: str
  display_class_prefix: str
  boot_vga_value: str


class DeviceIds(TypedDict):
  gsp_minimum: int
  legacy_minimum: int
  legacy_maximum_exclusive: int


class Settings(TypedDict):
  paths: Paths
  identifiers: Identifiers
  device_ids: DeviceIds


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid NVIDIA hardware configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid NVIDIA hardware configuration: {label} must be a non-empty string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError(f"invalid NVIDIA hardware configuration: {label} must be a non-negative integer")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-nvidia.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  paths = _mapping(document.get("paths"), "paths")
  identifiers = _mapping(document.get("identifiers"), "identifiers")
  device_ids = _mapping(document.get("device_ids"), "device_ids")
  return {
    "paths": {
      "pci_devices": _text(paths.get("pci_devices"), "paths.pci_devices"),
      "override_environment": _text(paths.get("override_environment"), "paths.override_environment"),
      "device_glob": _text(paths.get("device_glob"), "paths.device_glob"),
      "vendor_attribute": _text(paths.get("vendor_attribute"), "paths.vendor_attribute"),
      "class_attribute": _text(paths.get("class_attribute"), "paths.class_attribute"),
      "device_attribute": _text(paths.get("device_attribute"), "paths.device_attribute"),
      "boot_vga_attribute": _text(paths.get("boot_vga_attribute"), "paths.boot_vga_attribute"),
      "attribute_encoding": _text(paths.get("attribute_encoding"), "paths.attribute_encoding"),
    },
    "identifiers": {
      "vendor": _text(identifiers.get("vendor"), "identifiers.vendor"),
      "display_class_prefix": _text(identifiers.get("display_class_prefix"), "identifiers.display_class_prefix"),
      "boot_vga_value": _text(identifiers.get("boot_vga_value"), "identifiers.boot_vga_value"),
    },
    "device_ids": {
      "gsp_minimum": _integer(device_ids.get("gsp_minimum"), "device_ids.gsp_minimum"),
      "legacy_minimum": _integer(device_ids.get("legacy_minimum"), "device_ids.legacy_minimum"),
      "legacy_maximum_exclusive": _integer(device_ids.get("legacy_maximum_exclusive"), "device_ids.legacy_maximum_exclusive"),
    },
  }


def _has_nvidia_display(settings: Settings) -> bool:
  paths = settings["paths"]
  devices = Path(os.environ.get(paths["override_environment"], paths["pci_devices"]))
  for device in devices.glob(paths["device_glob"]):
    try:
      vendor = (device / paths["vendor_attribute"]).read_text(encoding=paths["attribute_encoding"]).strip()
      device_class = (device / paths["class_attribute"]).read_text(encoding=paths["attribute_encoding"]).strip()
    except (OSError, UnicodeError):
      continue
    if vendor == settings["identifiers"]["vendor"] and device_class.startswith(settings["identifiers"]["display_class_prefix"]):
      return True
  return False


def _has_nvidia_device_in_range(settings: Settings, minimum: int, maximum: int | None) -> bool:
  paths = settings["paths"]
  devices = Path(os.environ.get(paths["override_environment"], paths["pci_devices"]))
  for device in devices.glob(paths["device_glob"]):
    try:
      vendor = (device / paths["vendor_attribute"]).read_text(encoding=paths["attribute_encoding"]).strip()
      device_class = (device / paths["class_attribute"]).read_text(encoding=paths["attribute_encoding"]).strip()
      device_id_text = (device / paths["device_attribute"]).read_text(encoding=paths["attribute_encoding"]).strip()
    except (OSError, UnicodeError):
      continue
    if vendor != settings["identifiers"]["vendor"] or not device_class.startswith(settings["identifiers"]["display_class_prefix"]):
      continue
    try:
      device_id = int(device_id_text, 0)
    except ValueError:
      continue
    if device_id >= minimum and (maximum is None or device_id < maximum):
      return True
  return False


def _generation_main(
  minimum_key: Literal["gsp_minimum", "legacy_minimum"],
  maximum_key: Literal["legacy_maximum_exclusive"] | None,
) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load NVIDIA hardware configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    ids = settings["device_ids"]
    maximum = ids[maximum_key] if maximum_key is not None else None
    return 0 if _has_nvidia_device_in_range(settings, ids[minimum_key], maximum) else 1
  except OSError as error:
    print(f"Could not inspect PCI devices: {error}", file=sys.stderr)
    return 1


def gsp_main() -> int:
  return _generation_main("gsp_minimum", None)


def without_gsp_main() -> int:
  return _generation_main("legacy_minimum", "legacy_maximum_exclusive")


def _nvidia_drives_display(settings: Settings) -> bool:
  paths = settings["paths"]
  identifiers = settings["identifiers"]
  devices = Path(os.environ.get(paths["override_environment"], paths["pci_devices"]))
  nvidia_boot = False
  other_boot = False
  for device in devices.glob(paths["device_glob"]):
    try:
      device_class = (device / paths["class_attribute"]).read_text(encoding=paths["attribute_encoding"]).strip()
    except (OSError, UnicodeError):
      continue
    if not device_class.startswith(identifiers["display_class_prefix"]):
      continue
    try:
      vendor = (device / paths["vendor_attribute"]).read_text(encoding=paths["attribute_encoding"]).strip()
    except (OSError, UnicodeError):
      vendor = ""
    try:
      boot_vga = (device / paths["boot_vga_attribute"]).read_text(encoding=paths["attribute_encoding"]).strip()
    except (OSError, UnicodeError):
      boot_vga = ""
    if boot_vga == identifiers["boot_vga_value"]:
      if vendor == identifiers["vendor"]:
        nvidia_boot = True
      else:
        other_boot = True
  return not (other_boot and not nvidia_boot)


def nvidia_display_main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load NVIDIA hardware configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    return 0 if _nvidia_drives_display(settings) else 1
  except OSError as error:
    print(f"Could not inspect PCI devices: {error}", file=sys.stderr)
    return 1


def main() -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load NVIDIA hardware configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    return 0 if _has_nvidia_display(settings) else 1
  except OSError as error:
    print(f"Could not inspect PCI devices: {error}", file=sys.stderr)
    return 1
