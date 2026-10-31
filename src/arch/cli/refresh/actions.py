from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import cast

import yaml


def _settings() -> tuple[list[str], list[str], str, dict[str, int]]:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/refresh-tmux.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise ValueError("invalid tmux refresh configuration")
  document = cast(dict[object, object], raw)
  commands_raw = document.get("commands")
  messages_raw = document.get("messages")
  statuses_raw = document.get("statuses")
  if not all(isinstance(value, dict) for value in (commands_raw, messages_raw, statuses_raw)):
    raise ValueError("invalid tmux refresh configuration")
  commands = cast(dict[object, object], commands_raw)
  messages = cast(dict[object, object], messages_raw)
  statuses = cast(dict[object, object], statuses_raw)
  refresh = commands.get("refresh_config")
  restart = commands.get("restart_tmux")
  usage = messages.get("usage")
  if not isinstance(refresh, list) or not refresh or not all(isinstance(value, str) and value for value in refresh):
    raise ValueError("invalid tmux refresh command")
  if not isinstance(restart, list) or not restart or not all(isinstance(value, str) and value for value in restart):
    raise ValueError("invalid tmux restart command")
  if not isinstance(usage, str) or not usage:
    raise ValueError("invalid tmux refresh message")
  parsed_statuses = {
    name: statuses.get(name)
    for name in ("success", "failure", "invalid_arguments")
  }
  if not all(type(value) is int and 0 <= cast(int, value) <= 255 for value in parsed_statuses.values()):
    raise ValueError("invalid tmux refresh status codes")
  return (
    cast(list[str], refresh),
    cast(list[str], restart),
    usage,
    cast(dict[str, int], parsed_statuses),
  )


def tmux_main(arguments: list[str]) -> int:
  try:
    refresh_command, restart_command, usage, statuses = _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    return os.EX_CONFIG
  if arguments:
    print(usage, file=sys.stderr)
    return statuses["invalid_arguments"]
  refreshed = subprocess.run(refresh_command, check=False).returncode
  if refreshed != statuses["success"]:
    return refreshed
  restarted = subprocess.run(restart_command, check=False).returncode
  return statuses["success"] if restarted == statuses["success"] else statuses["failure"]
