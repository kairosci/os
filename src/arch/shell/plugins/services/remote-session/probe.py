#!/usr/bin/python3 -I

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import yaml


class Commands(TypedDict):
  process_search: list[str]


class Settings(TypedDict):
  proc_root_environment: str
  proc_root_default: str
  process_name: str
  pid_pattern: str
  process_name_file: str
  process_environment_file: str
  commands: Commands
  ssh_connection_prefix: str
  environment_record_separator: str
  peer_address_separator: str
  output_separator: str


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid remote-session configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid remote-session configuration: {label} must be a string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value:
    raise TypeError(f"invalid remote-session configuration: {label} must be a non-empty list")
  return [_text(item, f"{label} item") for item in value]


def settings() -> Settings:
  root = Path(os.environ["ARCH_PATH"])
  raw: object = yaml.safe_load((root / "data/shell/remote-session.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  commands = _mapping(config.get("commands"), "commands")
  pid_pattern = _text(config.get("pid_pattern"), "pid_pattern")
  try:
    re.compile(pid_pattern)
  except re.error as error:
    raise ValueError("invalid remote-session configuration: pid_pattern is not a valid pattern") from error
  return {
    "proc_root_environment": _text(config.get("proc_root_environment"), "proc_root_environment"),
    "proc_root_default": _text(config.get("proc_root_default"), "proc_root_default"),
    "process_name": _text(config.get("process_name"), "process_name"),
    "pid_pattern": pid_pattern,
    "process_name_file": _text(config.get("process_name_file"), "process_name_file"),
    "process_environment_file": _text(config.get("process_environment_file"), "process_environment_file"),
    "commands": {"process_search": _text_list(commands.get("process_search"), "commands.process_search")},
    "ssh_connection_prefix": _text(config.get("ssh_connection_prefix"), "ssh_connection_prefix"),
    "environment_record_separator": _text(config.get("environment_record_separator"), "environment_record_separator"),
    "peer_address_separator": _text(config.get("peer_address_separator"), "peer_address_separator"),
    "output_separator": _text(config.get("output_separator"), "output_separator"),
  }


def process_peer(environ_path: Path, config: Settings) -> str:
  try:
    records = environ_path.read_bytes().split(config["environment_record_separator"].encode())
  except OSError:
    return ""
  prefix = config["ssh_connection_prefix"].encode()
  separator = config["peer_address_separator"].encode()
  for record in records:
    if record.startswith(prefix):
      value = record[len(prefix):].split(separator, maxsplit=1)[0]
      return value.decode(encoding="utf-8", errors="replace")
  return ""


def main() -> int:
  try:
    config = settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load remote-session configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  proc_root = Path(os.environ.get(config["proc_root_environment"]) or config["proc_root_default"])
  pid_pattern = re.compile(config["pid_pattern"])
  try:
    search = subprocess.run(
      [*config["commands"]["process_search"], str(os.getuid()), config["process_name"]],
      check=False,
      capture_output=True,
      text=True,
    )
  except OSError:
    return 0
  if search.returncode != 0:
    return 0
  process_ids = sorted(
    {line.strip() for line in search.stdout.splitlines() if pid_pattern.fullmatch(line.strip())},
    key=int,
  )

  for process_id in process_ids:
    process = proc_root / process_id
    try:
      if process.stat().st_uid != os.getuid():
        continue
      process_name = (process / config["process_name_file"]).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
      continue
    if process_name != config["process_name"]:
      continue
    peer = process_peer(process / config["process_environment_file"], config)
    print(f"{process.name}{config['output_separator']}{peer}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
