from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/version-pkgs.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid package version configuration")
  return settings


def main() -> int:
  settings = _settings()
  log = settings["log"]
  path = Path(os.environ.get(log["path_environment"]) or log["default_path"])
  try:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
  except OSError:
    lines = []

  matching = [line for line in lines if log["match_text"] in line]
  latest = matching[-1] if matching else ""
  timestamp = latest
  match = re.search(log["timestamp_pattern"], latest)
  if match:
    timestamp = match.group(int(log["timestamp_group"]))

  locale_result = subprocess.run(settings["commands"]["locale"], check=False, stdout=subprocess.PIPE, text=True)
  locale_name = locale_result.stdout.rstrip("\n")
  language = locale_name.split(".", 1)[0].split("_", 1)[0]
  date_format = settings["commands"]["date_formats"].get(
    language,
    settings["commands"]["date_formats"][settings["commands"]["default_language"]],
  )
  environment = os.environ.copy()
  environment["LC_TIME"] = locale_name
  command = [argument.format(timestamp=timestamp, format=date_format) for argument in settings["commands"]["date"]]
  result = subprocess.run(command, check=False, env=environment)
  return result.returncode
