from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


def _messages(settings: dict[str, object], code: str) -> dict[str, str]:
  default = settings["default_language"]
  for source in (code, os.environ.get(settings["language_environment"], "")):
    language = source.split("-", 1)[0].split("_", 1)[0].lower()
    if language in settings["messages"]:
      return settings["messages"][language]
  return settings["messages"][default]


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/system-setup.yml").read_text(encoding="utf-8"))
  settings = config["language_setup"]
  marker = Path(os.environ.get(settings["marker_environment"]) or settings["marker_default"])
  try:
    code = marker.read_text(encoding="utf-8").splitlines()[0]
  except OSError:
    marker = Path(settings["fallback_marker"])
    try:
      code = marker.read_text(encoding="utf-8").splitlines()[0]
    except OSError:
      return 0
    except IndexError:
      return 0
  except IndexError:
    return 0
  if not code:
    return 0

  locales_path = Path(
    os.environ.get(settings["locales_file_environment"]) or root / settings["locales_file_default"]
  )
  try:
    locales = json.loads(locales_path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError):
    return 1
  if re.fullmatch(settings["code_pattern"], code) is None or code not in locales:
    message = _messages(settings, code)["invalid"].format(marker=marker, code=code)
    print(message, file=sys.stderr)
    return 0

  command = [part.format(arch_path=root) for part in settings["generator_command"]]
  return subprocess.run([*command, code], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
