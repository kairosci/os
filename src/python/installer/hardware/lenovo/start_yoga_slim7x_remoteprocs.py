"""Start the Yoga Slim 7x audio and compute DSP remote processors."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import time

import yaml


def load_config() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  return yaml.safe_load(
    (root / "data/installer/hardware/lenovo/yoga-slim7x.yml").read_text(encoding="utf-8"),
  )


def localized(messages: dict, key: str, **values: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  return messages.get(language, messages["en"])[key].format(**values)


def main() -> int:
  config = load_config()
  options = config["remoteproc"]
  root = Path(os.environ.get(options["root_environment"]) or options["root_default"])
  attempts = int(os.environ.get(options["attempts_environment"]) or options["attempts_default"])
  sleep_seconds = float(os.environ.get(options["sleep_environment"]) or options["sleep_default"])
  messages = config["messages"]
  started = {key: False for key in options["firmware_patterns"]}

  for attempt in range(attempts):
    for state_file in sorted(root.glob(options["state_glob"])):
      remoteproc = state_file.parent
      firmware_file = remoteproc / options["firmware_filename"]
      try:
        firmware = firmware_file.read_text(encoding="utf-8").strip("\0\n")
      except OSError:
        continue
      try:
        state = state_file.read_text(encoding="utf-8").strip("\0\n")
      except OSError:
        state = ""

      kind = next(
        (name for name, pattern in options["firmware_patterns"].items() if pattern in firmware),
        None,
      )
      if kind is None or started[kind]:
        continue

      if state == options["running_state"]:
        print(localized(messages, f"{kind}_already_running"))
      else:
        try:
          state_file.write_text(options["start_state"] + "\n", encoding="utf-8")
        except OSError:
          print(localized(messages, f"{kind}_failed", firmware=firmware), file=sys.stderr)
          continue
        print(localized(messages, f"{kind}_started"))
      started[kind] = True

    if all(started.values()):
      return int(config["statuses"]["complete"])
    if attempt + 1 < attempts:
      time.sleep(sleep_seconds)

  missing = "cdsp_missing" if started["adsp"] else "adsp_missing"
  print(localized(messages, missing), file=sys.stderr)
  return int(config["statuses"]["complete"] if started["adsp"] else config["statuses"]["failed"])


if __name__ == "__main__":
  raise SystemExit(main())
