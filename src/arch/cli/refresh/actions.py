from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import cast

import yaml


def _settings(action: str) -> tuple[list[str], list[str], str, dict[str, int]]:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/refresh-actions.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise ValueError("invalid config refresh configuration")
  document = cast(dict[object, object], raw)
  actions_raw = document.get("actions")
  statuses_raw = document.get("statuses")
  if not isinstance(actions_raw, dict) or not isinstance(statuses_raw, dict):
    raise ValueError("invalid config refresh configuration")
  actions = cast(dict[object, object], actions_raw)
  statuses = cast(dict[object, object], statuses_raw)
  action_raw = actions.get(action)
  if not isinstance(action_raw, dict):
    raise ValueError("invalid config refresh action")
  action_settings = cast(dict[object, object], action_raw)
  refresh = action_settings.get("refresh_config")
  restart = action_settings.get("restart")
  usage = action_settings.get("usage")
  if not isinstance(refresh, list) or not refresh or not all(isinstance(value, str) and value for value in refresh):
    raise ValueError("invalid config refresh command")
  if not isinstance(restart, list) or not restart or not all(isinstance(value, str) and value for value in restart):
    raise ValueError("invalid config refresh restart command")
  if not isinstance(usage, str) or not usage:
    raise ValueError("invalid config refresh message")
  parsed_statuses: dict[str, int] = {}
  for name in ("success", "failure", "invalid_arguments"):
    value = statuses.get(name)
    if type(value) is not int or not 0 <= value <= 255:
      raise ValueError("invalid config refresh status codes")
    parsed_statuses[name] = value
  return (
    cast(list[str], refresh),
    cast(list[str], restart),
    usage,
    parsed_statuses,
  )


def _main(action: str, arguments: list[str]) -> int:
  try:
    refresh_command, restart_command, usage, statuses = _settings(action)
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


def tmux_main(arguments: list[str]) -> int:
  return _main("tmux", arguments)


def hyprsunset_main(arguments: list[str]) -> int:
  return _main("hyprsunset", arguments)
