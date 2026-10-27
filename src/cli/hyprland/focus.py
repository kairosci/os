from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/hyprland-focus.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid Hyprland focus configuration")
  return settings


def _message(settings: dict[str, Any], key: str) -> str:
  language = os.environ.get("LANG", settings["default_language"]).split(".", 1)[0].split("_", 1)[0]
  translations = settings["messages"]
  language = language if language in translations else settings["default_language"]
  return translations[language][key]


def _history_order(client: dict[str, Any], field: str) -> tuple[bool, int]:
  value = client.get(field)
  try:
    return (value is not None, int(value))
  except (TypeError, ValueError):
    return (False, 0)


def main() -> int:
  settings = _settings()
  if len(sys.argv) < 2 or not sys.argv[1]:
    print(_message(settings, "usage"), file=sys.stderr)
    return settings["exit_codes"]["usage"]

  try:
    pattern = re.compile(sys.argv[1], re.IGNORECASE)
    result = subprocess.run(settings["client_command"], check=False, capture_output=True, text=True)
    clients = json.loads(result.stdout) if result.stdout else []
  except (OSError, json.JSONDecodeError, re.error):
    return settings["exit_codes"]["no_match"]
  if not isinstance(clients, list):
    return settings["exit_codes"]["no_match"]

  fields = settings["fields"]
  candidates = sorted(
    (client for client in clients if isinstance(client, dict)),
    key=lambda client: _history_order(client, fields["history"]),
  )
  address = next(
    (
      client.get(fields["address"])
      for client in candidates
      if isinstance(client.get(fields["class"]), str)
      and pattern.search(client[fields["class"]])
      and client.get(fields["address"])
    ),
    None,
  )
  if address is None:
    return settings["exit_codes"]["no_match"]

  for template in settings["dispatcher_commands"]:
    command = [argument.format(address=address) for argument in template]
    if subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
      return 0
  return settings["exit_codes"]["no_match"]


if __name__ == "__main__":
  raise SystemExit(main())
