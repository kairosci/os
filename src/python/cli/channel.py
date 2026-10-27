from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/channel.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError
  return settings


def _output(command: list[str]) -> tuple[int, str]:
  result = subprocess.run(command, check=False, capture_output=True, text=True)
  return result.returncode, result.stdout.strip()


def channel_current_main() -> int:
  settings = _settings()
  root = Path(os.environ["ARCH_PATH"])
  packaged_root = os.environ.get(
    settings["packaged_root_environment"],
    settings["packaged_root_default"],
  )
  if str(root).rstrip("/") != str(packaged_root).rstrip("/"):
    print(settings["development"])
    return 0

  status, _ = _output([*settings["commands"]["package_query"], *settings["development_packages"]])
  if status == 0:
    print(settings["edge"])
    return 0

  status, _ = _output([*settings["commands"]["package_query"], *settings["stable_packages"]])
  if status == 0:
    status, channel = _output([settings["commands"]["version_channel"]])
    if status == 0:
      channel = channel.split()[0] if channel else settings["unknown"]
      if channel in (settings["stable"], settings["release_candidate"]):
        print(channel)
      else:
        print(settings["unknown"])
    else:
      print(settings["unknown"])
    return 0

  print(settings["unknown"])
  return 0
