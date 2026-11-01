from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

import yaml


def _configuration() -> dict[str, object]:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/restart-xcompose.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise TypeError("restart configuration must be a mapping")
  return cast(dict[str, object], raw)


def _mapping(value: object, name: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"restart configuration {name} must be a mapping")
  return cast(dict[str, object], value)


def _command(value: object, uid: int) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
    raise ValueError("restart configuration commands must be non-empty string lists")
  return [part.replace("{uid}", str(uid)) for part in value]


def _integer(value: object, minimum: int) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
    raise ValueError("restart configuration limits must be positive integers")
  return value


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError("restart configuration messages must be non-empty strings")
  return value


def _run(command: list[str], timeout: int) -> subprocess.CompletedProcess[bytes]:
  return subprocess.run(command, check=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)


def main() -> int:
  try:
    config = _configuration()
    limits = _mapping(config.get("limits"), "limits")
    commands = _mapping(config.get("commands"), "commands")
    messages = _mapping(config.get("messages"), "messages")
    statuses = _mapping(config.get("statuses"), "statuses")
    timeout = _integer(limits.get("command_timeout_seconds"), 1)
    retries = _integer(limits.get("retry_count"), 1)
    interval = _integer(limits.get("poll_interval_milliseconds"), 1) / 1000
    failed = _integer(statuses.get("operation_failed"), 1)
    success = _integer(statuses.get("success"), 0)
    stop_error = _text(messages.get("process_stop_error"))
    uid = os.getuid()
    stop = _command(commands.get("stop_unit"), uid)
    kill = _command(commands.get("kill_process"), uid)
    present = _command(commands.get("process_presence"), uid)
    start = _command(commands.get("start_unit"), uid)
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Invalid XCompose restart configuration: {error}", file=sys.stderr)
    return 1

  def process_is_running() -> bool:
    result = _run(present, timeout)
    if result.returncode not in (0, 1):
      raise subprocess.CalledProcessError(result.returncode, present)
    return result.returncode == 0

  try:
    _run(stop, timeout).check_returncode()
    for attempt in range(retries):
      _run(kill, timeout)
      deadline = time.monotonic() + timeout
      while process_is_running() and time.monotonic() < deadline:
        time.sleep(min(interval, max(0, deadline - time.monotonic())))
      if not process_is_running():
        _run(start, timeout).check_returncode()
        return success
      if attempt + 1 < retries:
        _run(stop, timeout).check_returncode()
    print(stop_error, file=sys.stderr)
    return failed
  except (OSError, subprocess.SubprocessError) as error:
    print(f"{stop_error} ({error})", file=sys.stderr)
    return failed
