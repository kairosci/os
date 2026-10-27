from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/first-run.yml").read_text(encoding="utf-8"))
  step = config[sys.argv[1]]
  if "commands" not in step:
    language = os.environ.get("LANG", step["default_language"]).split(".", 1)[0].split("_", 1)[0]
    messages = step["messages"]
    language = language if language in messages else step["default_language"]
    message = messages[language]
    command = [*step["command"], message["title"], message["body"], *step["action"]]
    return subprocess.run(command, check=False).returncode

  commands = step["commands"]
  status = 0
  for command in commands:
    status = subprocess.run(command, check=False).returncode
  return status


if __name__ == "__main__":
  raise SystemExit(main())
