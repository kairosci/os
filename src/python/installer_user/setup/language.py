from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["language"]
  language_file = Path(settings["preset_file"])
  try:
    code = language_file.read_text(encoding="utf-8").splitlines()[0]
  except (OSError, IndexError):
    return 0
  if not code:
    return 0

  locale_code = os.environ.get("LANG", settings["default_language"]).split(".", 1)[0].split("_", 1)[0].lower()
  messages = settings["messages"].get(locale_code, settings["messages"][settings["default_language"]])
  command = settings["command"].format(arch_path=root)
  status = subprocess.run([command, *settings["arguments"], code], check=False).returncode
  if status != 0:
    print(messages["failure"].format(code=code), file=sys.stderr)
  return status


if __name__ == "__main__":
  raise SystemExit(main())
