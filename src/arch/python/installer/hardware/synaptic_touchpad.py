from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


def _run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str] | None:
  try:
    return subprocess.run(
      command,
      check=False,
      stdout=subprocess.PIPE if capture else None,
      text=True,
      stderr=subprocess.DEVNULL,
    )
  except OSError:
    return None


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["synaptic_touchpad"]
  devices = Path(os.environ.get(settings["device_file_environment"], settings["device_file_default"]))
  try:
    if re.search(settings["device_pattern"], devices.read_text(encoding="utf-8", errors="replace"), re.IGNORECASE) is None:
      return 0
  except OSError:
    return 0

  loaded = _run(settings["loaded_modules_command"], capture=True)
  loaded_pattern = re.compile(settings["loaded_module_pattern"], re.MULTILINE)
  if loaded is not None and loaded_pattern.search(loaded.stdout or ""):
    return 0
  resolved = _run(settings["resolve_module_command"])
  if resolved is None or resolved.returncode:
    return 0

  result = _run(settings["load_module_command"])
  if result is None or result.returncode:
    language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
    message = settings["messages"].get(language, settings["messages"]["en"])["load_failed"]
    print(message, file=sys.stderr)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
