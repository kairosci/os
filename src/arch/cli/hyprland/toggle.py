from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import sys

import yaml


def _toggle_path(name: str) -> Path:
  if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
    raise ValueError("toggle name must be a plain filename stem")
  settings_path = Path(os.environ["AP"]) / "data/cli/hyprland-toggle.yml"
  settings = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid Hyprland toggle configuration")
  directory = settings.get("home_relative_state_directory")
  suffix = settings.get("filename_suffix")
  if not isinstance(directory, str) or not directory or Path(directory).is_absolute() or ".." in Path(directory).parts:
    raise ValueError("invalid Hyprland toggle state directory")
  if not isinstance(suffix, str) or not suffix or "/" in suffix or "\\" in suffix:
    raise ValueError("invalid Hyprland toggle filename suffix")
  return Path(os.environ["HOME"]) / directory / f"{name}{suffix}"


def _main(args: list[str], enabled: bool) -> int:
  if len(args) != 1:
    print("Usage: archctl hyprland toggle enabled|disabled <flag-name>", file=sys.stderr)
    return 2
  try:
    path = _toggle_path(args[0])
    try:
      mode = path.stat().st_mode
      exists = stat.S_ISREG(mode)
    except FileNotFoundError:
      exists = False
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    print("Could not read Hyprland toggle state", file=sys.stderr)
    return os.EX_CONFIG
  return 0 if exists == enabled else 1


def enabled_main(args: list[str]) -> int:
  return _main(args, True)


def disabled_main(args: list[str]) -> int:
  return _main(args, False)
