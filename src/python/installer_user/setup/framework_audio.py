from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["framework_audio_setup"]
  try:
    result = subprocess.run(settings["list_command"], check=False, capture_output=True, text=True)
  except OSError:
    return 0
  if result.returncode:
    return 0

  lines = result.stdout.splitlines()
  family = re.compile(settings["family_pattern"])
  name = re.compile(settings["name_pattern"])
  context = int(settings["context_lines"])
  cards: list[str] = []
  for index, line in enumerate(lines):
    if family.search(line):
      start = max(0, index - context)
      for candidate in lines[start : index + 1]:
        match = name.search(candidate)
        if match and match.group(1) not in cards:
          cards.append(match.group(1))
  if cards:
    command = [argument.format(card="\n".join(cards)) for argument in settings["profile_command"]]
    try:
      subprocess.run(command, check=False, stderr=subprocess.DEVNULL)
    except OSError:
      pass
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
