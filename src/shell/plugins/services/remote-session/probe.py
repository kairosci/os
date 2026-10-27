#!/usr/bin/python3 -I

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml


def settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/shell/remote-session.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError
  return config


def process_peer(environ_path: Path, config: dict[str, Any]) -> str:
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
  config = settings()
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
