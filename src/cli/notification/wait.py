from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import yaml


def _config() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/notification-wait.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid notification wait configuration")
  return config


def _ready(config: dict) -> bool:
  for command in config["probe_commands"]:
    try:
      status = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode
    except OSError:
      return False
    if status != 0:
      return False
  return True


def _message(config: dict, key: str) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  messages = config["messages"]
  language = language if language in messages else config["default_language"]
  return messages[language][key]


def main() -> int:
  config = _config()
  if len(sys.argv) > config["argument_counts"]["maximum"]:
    print(_message(config, "usage"), file=sys.stderr)
    return config["exit_codes"]["usage"]

  try:
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else config["default_timeout_seconds"]
  except ValueError:
    print(_message(config, "invalid_timeout"), file=sys.stderr)
    return config["exit_codes"]["invalid_timeout"]
  if timeout < 0 or timeout > config["maximum_timeout_seconds"]:
    print(_message(config, "invalid_timeout"), file=sys.stderr)
    return config["exit_codes"]["invalid_timeout"]

  deadline = time.monotonic() + timeout
  while time.monotonic() < deadline:
    if _ready(config):
      return 0
    remaining = deadline - time.monotonic()
    if remaining > 0:
      time.sleep(min(config["probe_interval_seconds"], remaining))
  return config["exit_codes"]["timeout"]


if __name__ == "__main__":
  raise SystemExit(main())
