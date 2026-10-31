"""Check the shared sleep-disable setting."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  directory_environment: str
  directory_default: str
  disabled_filename: str
  statuses: dict[str, int]


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  value: object = yaml.safe_load((root / "data/system/sleep.yml").read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("invalid sleep configuration")
  return cast(Settings, value)


def is_disabled() -> bool:
  settings = _settings()
  directory = os.environ.get(settings["directory_environment"]) or settings["directory_default"]
  return (Path(directory) / settings["disabled_filename"]).is_file()


def main() -> int:
  settings = _settings()
  disabled = is_disabled()
  status = "complete" if disabled else "enabled"
  return settings["statuses"][status]
