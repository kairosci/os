from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import yaml


def _language(config: dict[str, object]) -> str:
  default_language = cast(str, config["default_language"])
  settings = cast(dict[str, object], config["orchestrator"])
  messages = cast(dict[str, object], settings["messages"])
  language = os.environ.get("LANG", default_language).split(".", 1)[0].split("_", 1)[0]
  return language if language in messages else default_language


def _command(template: list[str], root: Path, settings: dict[str, object]) -> list[str]:
  completion_marker = cast(str, settings["completion_marker"])
  return [part.format(arch_path=root, completion_marker=completion_marker) for part in template]


def _log(path: Path, timestamp_format: str, message: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  descriptor = os.open(
    path,
    os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
    0o600,
  )
  os.fchmod(descriptor, 0o600)
  with os.fdopen(descriptor, "a", encoding="utf-8") as output:
    timestamp = datetime.datetime.now().strftime(timestamp_format)
    output.write(f"[{timestamp}] {message}\n")


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = cast(dict[str, object], yaml.safe_load((root / "data/installer/first-run.yml").read_text(encoding="utf-8")))
  settings = cast(dict[str, object], config["orchestrator"])
  language = _language(config)
  messages = cast(dict[str, dict[str, str]], settings["messages"])[language]

  parser = argparse.ArgumentParser(prog=cast(str, settings["command_name"]), description=messages["description"])
  force_option = cast(str, settings["force_option"])
  parser.add_argument(force_option, action="store_true", help=messages["force_help"])
  options = parser.parse_args()

  state = Path.home() / cast(str, settings["state_directory"])
  log_path = state / cast(str, settings["log_file"])
  done = subprocess.run(_command(cast(list[str], settings["done_check"]), root, settings), check=False).returncode == 0
  if done and not options.force:
    print(messages["already_complete"])
    return 0

  provision = list(cast(list[str], settings["provision_user"]))
  if options.force:
    provision.append(force_option)
  subprocess.run(provision, check=False)

  failed = False
  message_tree = cast(dict[str, object], settings["messages"])
  labels = cast(dict[str, dict[str, str]], message_tree["steps"])[language]
  timestamp_format = cast(str, settings["timestamp_format"])
  notification_wait_before = cast(str, settings["notification_wait_before"])
  for step in cast(list[dict[str, object]], settings["steps"]):
    if step["id"] == notification_wait_before:
      notification_status = subprocess.run(cast(list[str], settings["notification_wait"]), check=False).returncode
      if notification_status != 0:
        _log(log_path, timestamp_format, messages["notification_timeout"])

    step_id = cast(str, step["id"])
    label = labels[step_id]
    _log(log_path, timestamp_format, messages["starting"].format(step=label))
    status = subprocess.run(_command(cast(list[str], step["command"]), root, settings), check=False).returncode
    if status == 0:
      _log(log_path, timestamp_format, messages["completed"].format(step=label))
    else:
      failed = True
      _log(
        log_path,
        timestamp_format,
        messages["failed"].format(step=label, status=status),
      )

  if failed:
    _log(log_path, timestamp_format, messages["retry"])
  else:
    return subprocess.run(_command(cast(list[str], settings["done_mark"]), root, settings), check=False).returncode
  return 0
