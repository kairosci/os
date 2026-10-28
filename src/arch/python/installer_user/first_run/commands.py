from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = cast(dict[str, object], yaml.safe_load((root / "data/installer/first-run.yml").read_text(encoding="utf-8")))
  action = sys.argv[1]
  if action == "wifi_worker":
    return announce_network(config)
  if action == "user_units":
    return enable_user_units(config)

  step = cast(dict[str, object], config[action])
  if action == "wifi":
    subprocess.Popen(
      [sys.executable, "-I", str(Path(__file__).resolve()), cast(str, step["worker"])],
      stdin=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      start_new_session=True,
    )
    return 0
  if "messages" in step:
    return notify(config, step)

  commands = cast(list[list[str]], step["commands"])
  status = 0
  for command in commands:
    status = subprocess.run(command, check=False).returncode
  return status


def notify(config: dict[str, object], step: dict[str, object]) -> int:
  default_language = cast(str, config["default_language"])
  language = os.environ.get("LANG", default_language).split(".", 1)[0].split("_", 1)[0]
  translations = cast(dict[str, dict[str, str]], step["messages"])
  language = language if language in translations else default_language
  message = translations[language]
  command = [*cast(list[str], step["command"]), message["title"], message["body"], *cast(list[str], step["action"])]
  return subprocess.run(command, check=False).returncode


def announce_network(config: dict[str, object]) -> int:
  wifi = cast(dict[str, object], config["wifi"])
  network = cast(dict[str, object], wifi["network"])
  update = cast(dict[str, object], wifi["update"])
  subprocess.run(cast(list[str], network["startup_wait"]), check=False)
  if subprocess.run(cast(list[str], network["connectivity_check"]), check=False).returncode != 0:
    notify(config, cast(dict[str, object], wifi["wifi_notification"]))
    if subprocess.run(cast(list[str], network["connection_wait"]), check=False).returncode != 0:
      return 0

  check = subprocess.run(cast(list[str], update["check"]), check=False)
  if check.returncode == cast(int, update["no_updates_status"]):
    if os.environ["AP"] == cast(str, update["installed_path"]):
      return 0
    check = subprocess.run(cast(list[str], update["checkout_check"]), check=False)
    if check.returncode != 0:
      return 0
  return notify(config, cast(dict[str, object], wifi["update_notification"]))


def enable_user_units(config: dict[str, object]) -> int:
  settings = cast(dict[str, object], config["user_units"])
  input_method = subprocess.run(cast(list[str], settings["input_method"]), check=False)
  if input_method.returncode != 0:
    default_language = cast(str, config["default_language"])
    language = os.environ.get("LANG", default_language).split(".", 1)[0].split("_", 1)[0]
    messages = cast(dict[str, str], settings["messages"])
    language = language if language in messages else default_language
    print(messages[language], file=sys.stderr)

  reload_status = subprocess.run(cast(list[str], settings["daemon_reload"]), check=False).returncode
  if reload_status != 0:
    return reload_status

  failed = False
  for unit in cast(list[str], settings["units"]):
    command = [*cast(list[str], settings["enable"]), unit]
    if subprocess.run(command, check=False).returncode != 0:
      failed = True
  return int(failed)


if __name__ == "__main__":
  raise SystemExit(main())
