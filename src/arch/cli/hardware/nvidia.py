from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import TypedDict

import yaml


class Paths(TypedDict):
  pci_devices: str
  override_environment: str


class Identifiers(TypedDict):
  vendor: str
  display_class_prefix: str


class Settings(TypedDict):
  paths: Paths
  identifiers: Identifiers


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid NVIDIA hardware configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid NVIDIA hardware configuration: {label} must be a non-empty string")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-nvidia.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  paths = _mapping(document.get("paths"), "paths")
  identifiers = _mapping(document.get("identifiers"), "identifiers")
  return {
    "paths": {
      "pci_devices": _text(paths.get("pci_devices"), "paths.pci_devices"),
      "override_environment": _text(paths.get("override_environment"), "paths.override_environment"),
    },
    "identifiers": {
      "vendor": _text(identifiers.get("vendor"), "identifiers.vendor"),
      "display_class_prefix": _text(identifiers.get("display_class_prefix"), "identifiers.display_class_prefix"),
    },
  }


def _has_nvidia_display(settings: Settings) -> bool:
  paths = settings["paths"]
  devices = Path(os.environ.get(paths["override_environment"], paths["pci_devices"]))
  for device in devices.iterdir():
    try:
      vendor = (device / "vendor").read_text(encoding="ascii").strip()
      device_class = (device / "class").read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
      continue
    if vendor == settings["identifiers"]["vendor"] and device_class.startswith(settings["identifiers"]["display_class_prefix"]):
      return True
  return False


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
