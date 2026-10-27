from __future__ import annotations

import locale
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/fonts.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid font command configuration")
  return settings


def current_main() -> int:
  settings = _settings()
  result = subprocess.run(settings["commands"]["current"], check=False, stdout=subprocess.PIPE, text=True)
  lines = result.stdout.splitlines()
  first = lines[0] if lines else ""
  separator = settings["current"]["family_separator"]
  index = int(settings["current"]["family_index"])
  fields = first.split(separator)
  if len(fields) > index:
    print(fields[index])
  return 0


def list_main() -> int:
  settings = _settings()
  locale.setlocale(locale.LC_COLLATE, "")
  result = subprocess.run(settings["commands"]["list"], check=False, stdout=subprocess.PIPE, text=True)
  excluded = re.compile(settings["list"]["exclude_pattern"], re.IGNORECASE)
  families: dict[str, str] = {}
  for line in result.stdout.splitlines():
    if line and not excluded.search(line):
      families.setdefault(locale.strxfrm(line), line)
  for key in sorted(families):
    print(families[key])
  return 0


if __name__ == "__main__":
  command = sys.argv[1] if len(sys.argv) > 1 else ""
  if command == "current":
    raise SystemExit(current_main())
  if command == "list":
    raise SystemExit(list_main())
  raise SystemExit(2)
