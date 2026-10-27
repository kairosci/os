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


def cjk_main(arguments: list[str]) -> int:
  settings = _settings()
  options = settings["cjk"]
  if not arguments:
    config_home = os.environ.get(options["config_home_environment"]) or str(Path.home() / options["config_home_default"])
    preference = Path(config_home) / options["preference_path"]
    variant = ""
    if preference.is_file():
      pattern = re.compile(options["preference_pattern"])
      for line in preference.read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if match:
          variant = match.group(options["preference_group"]).lower()
          break
    print(variant or options["default_variant"])
    return 0

  variant = arguments[0]
  if variant in options["help_arguments"]:
    language = os.environ.get("LANG", options["messages"]["default_language"]).split(".", 1)[0].split("_", 1)[0]
    messages = options["messages"]["usage"]
    print(messages.get(language, messages[options["messages"]["default_language"]]))
    return 0
  if variant not in options["variants"] or len(arguments) != 1:
    language = os.environ.get("LANG", options["messages"]["default_language"]).split(".", 1)[0].split("_", 1)[0]
    messages = options["messages"]["usage"]
    print(messages.get(language, messages[options["messages"]["default_language"]]), file=sys.stderr)
    return int(options["exit_codes"]["usage"])

  root = Path(os.environ["ARCH_PATH"])
  configure = options["configure"]
  result = subprocess.run(
    [configure["python"], str(root / configure["script"]), *configure["arguments"], variant],
    check=False,
  )
  if result.returncode != 0:
    return result.returncode

  result = subprocess.run(options["restart_command"], check=False)
  if result.returncode != 0:
    return result.returncode

  message = subprocess.run(
    [*options["i18n_command"], options["changed_message"]],
    check=False,
    capture_output=True,
    text=True,
  )
  restart_message = subprocess.run(
    [*options["i18n_command"], options["restart_apps_message"]],
    check=False,
    capture_output=True,
    text=True,
  )
  result = subprocess.run(
    [
      *options["notification_command"],
      options["notification_glyph"],
      message.stdout.rstrip("\n"),
      restart_message.stdout.rstrip("\n"),
    ],
    check=False,
  )
  return result.returncode


if __name__ == "__main__":
  command = sys.argv[1] if len(sys.argv) > 1 else ""
  if command == "current":
    raise SystemExit(current_main())
  if command == "list":
    raise SystemExit(list_main())
  if command == "cjk":
    raise SystemExit(cjk_main(sys.argv[2:]))
  raise SystemExit(2)
