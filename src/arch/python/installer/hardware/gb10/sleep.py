"""Disable system sleep on NVIDIA GB10 systems."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
from typing import TypedDict, cast

import yaml


class SleepConfig(TypedDict):
  directory_environment: str
  directory_default: str
  disabled_filename: str
  disabled_content: str
  hardware_check: list[str]
  install_file: list[str]
  statuses: dict[str, int]


def load_config() -> SleepConfig:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/system/sleep.yml").read_text(encoding="utf-8"))
  return cast(SleepConfig, config)


def config_path(config: SleepConfig) -> Path:
  directory = os.environ.get(config["directory_environment"]) or config["directory_default"]
  return Path(directory) / config["disabled_filename"]


def main() -> int:
  config = load_config()
  if subprocess.run(config["hardware_check"], check=False).returncode != int(config["statuses"]["complete"]):
    return int(config["statuses"]["complete"])

  target = config_path(config)
  if target.is_file():
    return int(config["statuses"]["complete"])
  with tempfile.TemporaryDirectory() as temporary_directory:
    source = Path(temporary_directory) / target.name
    source.write_text(config["disabled_content"], encoding="utf-8")
    subprocess.run([*config["install_file"], str(source), str(target)], check=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
