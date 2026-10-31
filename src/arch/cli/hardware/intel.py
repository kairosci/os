from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from collections.abc import Callable
from typing import TypedDict

import yaml


class Commands(TypedDict):
  pci_devices: list[str]


class Cpu(TypedDict):
  vendor_key: str
  vendor_id: str


class Devices(TypedDict):
  display_classes: list[str]
  panther_lake: str
  audio_classes: list[str]
  intel_vendor: str


class Settings(TypedDict):
  paths: dict[str, str]
  commands: Commands
  cpu: Cpu
  devices: Devices


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid Intel hardware configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid Intel hardware configuration: {label} must be a non-empty string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
    raise ValueError(f"invalid Intel hardware configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hardware-intel.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "root")
  paths = _mapping(document.get("paths"), "paths")
  commands = _mapping(document.get("commands"), "commands")
  cpu = _mapping(document.get("cpu"), "cpu")
  devices = _mapping(document.get("devices"), "devices")
  return {
    "paths": {"cpu_info": _text(paths.get("cpu_info"), "paths.cpu_info")},
    "commands": {"pci_devices": _text_list(commands.get("pci_devices"), "commands.pci_devices")},
    "cpu": {
      "vendor_key": _text(cpu.get("vendor_key"), "cpu.vendor_key"),
      "vendor_id": _text(cpu.get("vendor_id"), "cpu.vendor_id"),
    },
    "devices": {
      "display_classes": _text_list(devices.get("display_classes"), "devices.display_classes"),
      "panther_lake": _text(devices.get("panther_lake"), "devices.panther_lake").lower(),
      "audio_classes": _text_list(devices.get("audio_classes"), "devices.audio_classes"),
      "intel_vendor": _text(devices.get("intel_vendor"), "devices.intel_vendor").lower(),
    },
  }


def _has_intel_cpu(settings: Settings) -> bool:
  try:
    lines = Path(settings["paths"]["cpu_info"]).read_text(encoding="ascii").splitlines()
  except (OSError, UnicodeError):
    return False
  for line in lines:
    key, separator, value = line.partition(":")
    if separator and key.strip() == settings["cpu"]["vendor_key"]:
      return value.strip() == settings["cpu"]["vendor_id"]
  return False


def _pci_lines(settings: Settings) -> list[str]:
  result = subprocess.run(settings["commands"]["pci_devices"], check=False, capture_output=True, text=True)
  return result.stdout.splitlines() if result.returncode == 0 else []


def _has_panther_lake_gpu(settings: Settings) -> bool:
  devices = settings["devices"]
  for line in _pci_lines(settings):
    lowered = line.lower()
    if devices["panther_lake"] in lowered and any(device_class in lowered for device_class in devices["display_classes"]):
      return True
  return False


def _has_intel_sof_dsp(settings: Settings) -> bool:
  devices = settings["devices"]
  for line in _pci_lines(settings):
    lowered = line.lower()
    vendor_index = lowered.find(devices["intel_vendor"])
    if vendor_index >= 0 and any(
      0 <= lowered.find(device_class) < vendor_index for device_class in devices["audio_classes"]
    ):
      return True
  return False


def _main(predicate: Callable[[Settings], bool]) -> int:
  try:
    settings = _settings()
    result = predicate(settings)
  except (KeyError, OSError, UnicodeError, TypeError, ValueError, subprocess.SubprocessError, yaml.YAMLError) as error:
    print(f"Could not detect Intel hardware: {error}", file=sys.stderr)
    return os.EX_CONFIG
  return 0 if result else 1


def intel_main() -> int:
  return _main(_has_intel_cpu)


def intel_ptl_main() -> int:
  return _main(_has_panther_lake_gpu)


def intel_sof_main() -> int:
  return _main(_has_intel_sof_dsp)
