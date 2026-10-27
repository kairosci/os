from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/first-run.yml").read_text(encoding="utf-8"))
  action = sys.argv[1]
  if action == "wifi_worker":
    return announce_network(config)
  if action == "user_units":
    return enable_user_units(config)

  step = config[action]
  if action == "wifi":
    subprocess.Popen(
      [sys.executable, "-I", str(Path(__file__).resolve()), step["worker"]],
      stdin=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      start_new_session=True,
    )
    return 0
  if "messages" in step:
    return notify(config, step)

  commands = step["commands"]
  status = 0
  for command in commands:
    status = subprocess.run(command, check=False).returncode
  return status


def notify(config: dict, step: dict) -> int:
  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  translations = step["messages"]
  language = language if language in translations else config["default_language"]
  message = translations[language]
  command = [*step["command"], message["title"], message["body"], *step["action"]]
  return subprocess.run(command, check=False).returncode


def announce_network(config: dict) -> int:
  wifi = config["wifi"]
  network = wifi["network"]
  update = wifi["update"]
  subprocess.run(network["startup_wait"], check=False)
  if subprocess.run(network["connectivity_check"], check=False).returncode != 0:
    notify(config, wifi["wifi_notification"])
    if subprocess.run(network["connection_wait"], check=False).returncode != 0:
      return 0

  check = subprocess.run(update["check"], check=False)
  if check.returncode == update["no_updates_status"]:
    if os.environ["ARCH_PATH"] == update["installed_path"]:
      return 0
    check = subprocess.run(update["checkout_check"], check=False)
    if check.returncode != 0:
      return 0
  return notify(config, wifi["update_notification"])


def enable_user_units(config: dict) -> int:
  settings = config["user_units"]
  input_method = subprocess.run(settings["input_method"], check=False)
  if input_method.returncode != 0:
    language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
    messages = settings["messages"]
    language = language if language in messages else config["default_language"]
    print(messages[language], file=sys.stderr)

  reload_status = subprocess.run(settings["daemon_reload"], check=False).returncode
  if reload_status != 0:
    return reload_status

  failed = False
  for unit in settings["units"]:
    command = [*settings["enable"], unit]
    if subprocess.run(command, check=False).returncode != 0:
      failed = True
  return int(failed)


if __name__ == "__main__":
  raise SystemExit(main())
