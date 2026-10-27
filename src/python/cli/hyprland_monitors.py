from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load(
    (root / "data/cli/hyprland-monitors.yml").read_text(encoding="utf-8")
  )
  if not isinstance(settings, dict):
    raise ValueError("invalid Hyprland monitor configuration")
  return settings


def _monitors(settings: dict[str, Any], command: str) -> list[Any] | None:
  result = subprocess.run(
    settings["commands"][command]["command"], check=False, capture_output=True, text=True
  )
  if not result.stdout:
    return None
  monitors = json.loads(result.stdout)
  return monitors if isinstance(monitors, list) else []


def focused_main() -> int:
  settings = _settings()
  command = settings["commands"]["focused"]
  try:
    monitors = _monitors(settings, "focused")
  except json.JSONDecodeError:
    return settings["exit_codes"]["invalid_json"]["focused"]
  if monitors is None:
    return 0
  for monitor in monitors:
    if (
      isinstance(monitor, dict)
      and monitor.get(command["selected_field"]) == command["selected_value"]
    ):
      print(monitor.get(settings["output_field"]))
  return 0


def laptop_main() -> int:
  settings = _settings()
  command = settings["commands"]["laptop"]
  try:
    monitors = _monitors(settings, "laptop")
  except json.JSONDecodeError:
    return settings["exit_codes"]["invalid_json"]["laptop"]
  if monitors is None:
    return 0
  pattern = re.compile(command["name_pattern"])
  for monitor in monitors:
    name = monitor.get(settings["output_field"]) if isinstance(monitor, dict) else None
    if isinstance(name, str) and pattern.search(name):
      print(name)
      if command["first_match"]:
        break
  return 0
