from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

import yaml


def _language(config: dict) -> str:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  return language if language in config["orchestrator"]["messages"] else config["default_language"]


def _command(template: list[str], root: Path, settings: dict) -> list[str]:
  return [part.format(arch_path=root, completion_marker=settings["completion_marker"]) for part in template]


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
  config = yaml.safe_load((root / "data/installer/first-run.yml").read_text(encoding="utf-8"))
  settings = config["orchestrator"]
  language = _language(config)
  messages = settings["messages"][language]

  parser = argparse.ArgumentParser(prog=settings["command_name"], description=messages["description"])
  parser.add_argument(settings["force_option"], action="store_true", help=messages["force_help"])
  options = parser.parse_args()

  state = Path.home() / settings["state_directory"]
  log_path = state / settings["log_file"]
  done = subprocess.run(_command(settings["done_check"], root, settings), check=False).returncode == 0
  if done and not options.force:
    print(messages["already_complete"])
    return 0

  provision = list(settings["provision_user"])
  if options.force:
    provision.append(settings["force_option"])
  subprocess.run(provision, check=False)

  failed = False
  labels = settings["messages"]["steps"][language]
  for step in settings["steps"]:
    if step["id"] == settings["notification_wait_before"]:
      notification_status = subprocess.run(settings["notification_wait"], check=False).returncode
      if notification_status != 0:
        _log(log_path, settings["timestamp_format"], messages["notification_timeout"])

    label = labels[step["id"]]
    _log(log_path, settings["timestamp_format"], messages["starting"].format(step=label))
    status = subprocess.run(_command(step["command"], root, settings), check=False).returncode
    if status == 0:
      _log(log_path, settings["timestamp_format"], messages["completed"].format(step=label))
    else:
      failed = True
      _log(
        log_path,
        settings["timestamp_format"],
        messages["failed"].format(step=label, status=status),
      )

  if failed:
    _log(log_path, settings["timestamp_format"], messages["retry"])
  else:
    return subprocess.run(_command(settings["done_mark"], root, settings), check=False).returncode
  return 0
