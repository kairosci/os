from __future__ import annotations

import os
import sys
from pathlib import Path
from string import Template

import yaml


def _quote(value: str) -> str:
  return value.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["xcompose"]
  values = {
    "user_name": os.environ.get(settings["user_name_environment"], ""),
    "user_email": os.environ.get(settings["user_email_environment"], ""),
  }
  if any(any(ord(character) < 32 or ord(character) == 127 for character in value) for value in values.values()):
    language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
    messages = settings["messages"]
    message = messages.get(language, messages["en"])["invalid_identity"]
    print(message, file=sys.stderr)
    return 2

  values["ap"] = str(root)
  output = Template(settings["template"]).substitute(
    {key: _quote(value) for key, value in values.items()}
  )
  (Path.home() / settings["path"]).write_text(output + "\n", encoding="utf-8")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
