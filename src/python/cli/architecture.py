from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/architecture.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid architecture configuration")
  return settings


def _platform(settings: dict[str, Any]) -> str | None:
  root = Path(os.environ["ARCH_PATH"])
  command = settings["commands"]["platform_detector"]
  detector = [str(root / command[0]), *command[1:]]
  try:
    result = subprocess.run(detector, check=False, capture_output=True, text=True)
  except OSError:
    return None
  if result.returncode != 0:
    return None
  return result.stdout.strip()


def x86_main() -> int:
  settings = _settings()
  return 0 if _platform(settings) == settings["platforms"]["x86"] else 1


def aarch64_main() -> int:
  settings = _settings()
  platform = _platform(settings)
  if platform is None:
    return 1
  return 0 if platform.startswith(settings["platforms"]["aarch64_prefix"]) else 1
