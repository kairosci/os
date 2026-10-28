from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["platform_setup"]
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = settings["messages"]
  image_root = Path(os.environ.get(settings["image_root_environment"]) or "/")
  if (image_root / settings["image_marker"]).exists():
    print(messages.get(language, messages["en"])["image_deferred"])
    return 0
  return subprocess.run(settings["command"], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
