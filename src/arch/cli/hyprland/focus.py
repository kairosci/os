from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import yaml


class Fields(TypedDict):
  class_name: str
  history: str
  address: str


class ExitCodes(TypedDict):
  usage: int
  no_match: int


class FocusSettings(TypedDict):
  default_language: str
  client_command: list[str]
  fields: Fields
  dispatcher_commands: list[list[str]]
  exit_codes: ExitCodes
  messages: dict[str, dict[str, str]]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid Hyprland focus configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid Hyprland focus configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid Hyprland focus configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid Hyprland focus configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _settings() -> FocusSettings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hyprland-focus.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  fields = _mapping(settings.get("fields"), "fields")
  codes = _mapping(settings.get("exit_codes"), "exit_codes")
  raw_messages = _mapping(settings.get("messages"), "messages")
  messages: dict[str, dict[str, str]] = {}
  for language, raw_table in raw_messages.items():
    locale = _text(language, "messages language")
    table = _mapping(raw_table, f"messages.{locale}")
    messages[locale] = {
      _text(key, f"messages.{locale} key"): _text(value, f"messages.{locale} value")
      for key, value in table.items()
    }
  raw_dispatchers = settings.get("dispatcher_commands")
  if not isinstance(raw_dispatchers, list):
    raise ValueError("invalid Hyprland focus configuration: dispatcher_commands must be a list")
  dispatchers = [
    _text_list(command, f"dispatcher_commands[{index}]")
    for index, command in enumerate(raw_dispatchers)
  ]
  return {
    "default_language": _text(settings.get("default_language"), "default_language"),
    "client_command": _text_list(settings.get("client_command"), "client_command"),
    "fields": {
      "class_name": _text(fields.get("class"), "fields.class"),
      "history": _text(fields.get("history"), "fields.history"),
      "address": _text(fields.get("address"), "fields.address"),
    },
    "dispatcher_commands": dispatchers,
    "exit_codes": {
      "usage": _integer(codes.get("usage"), "exit_codes.usage"),
      "no_match": _integer(codes.get("no_match"), "exit_codes.no_match"),
    },
    "messages": messages,
  }


def _message(settings: FocusSettings, key: str) -> str:
  language = os.environ.get("LANG", settings["default_language"]).split(".", 1)[0].split("_", 1)[0]
  translations = settings["messages"]
  selected_language = language if language in translations else settings["default_language"]
  return translations[selected_language][key]


def _history_order(client: dict[str, object], field: str) -> tuple[bool, int]:
  value = client.get(field)
  if not isinstance(value, (int, str)) or isinstance(value, bool):
    return (False, 0)
  try:
    return (True, int(value))
  except ValueError:
    return (False, 0)


def main() -> int:
  try:
    settings = _settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load Hyprland focus configuration: {error}", file=sys.stderr)
    return 1
  if len(sys.argv) < 2 or not sys.argv[1]:
    print(_message(settings, "usage"), file=sys.stderr)
    return settings["exit_codes"]["usage"]

  try:
    pattern = re.compile(sys.argv[1], re.IGNORECASE)
    result = subprocess.run(settings["client_command"], check=False, capture_output=True, text=True)
    raw_clients: object = json.loads(result.stdout) if result.stdout else []
  except (OSError, json.JSONDecodeError, re.error):
    return settings["exit_codes"]["no_match"]
  if not isinstance(raw_clients, list):
    return settings["exit_codes"]["no_match"]
  clients = [
    {key: value for key, value in client.items()}
    for client in raw_clients
    if isinstance(client, dict) and all(isinstance(key, str) for key in client)
  ]

  fields = settings["fields"]
  candidates = sorted(clients, key=lambda client: _history_order(client, fields["history"]))
  address = None
  for client in candidates:
    class_name = client.get(fields["class_name"])
    client_address = client.get(fields["address"])
    if isinstance(class_name, str) and isinstance(client_address, str) and client_address:
      if pattern.search(class_name):
        address = client_address
        break
  if address is None:
    return settings["exit_codes"]["no_match"]

  for template in settings["dispatcher_commands"]:
    command = [argument.replace("{address}", address) for argument in template]
    if subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
      return 0
  return settings["exit_codes"]["no_match"]


if __name__ == "__main__":
  raise SystemExit(main())
