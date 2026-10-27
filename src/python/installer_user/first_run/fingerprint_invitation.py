from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/first-run.yml").read_text(encoding="utf-8"))
  invitation = config["fingerprint_invitation"]
  if subprocess.run(invitation["hardware_check"], check=False).returncode != 0:
    return 0
  if Path(invitation["pam_file"]).is_file():
    return 0
  if subprocess.run(invitation["marker"], check=False).returncode != 0:
    return 0

  language = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  messages = invitation["notification"]["messages"]
  language = language if language in messages else config["default_language"]
  message = messages[language]
  command = [
    *invitation["notification"]["command"],
    message["title"],
    message["body"],
    *invitation["notification"]["action"],
  ]
  return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
