from __future__ import annotations

import csv
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import yaml


class Actions(TypedDict):
  create: str
  restore: str


class Commands(TypedDict):
  command_presence: list[str]
  version: list[str]
  list_configs: list[str]
  create: list[str]
  cleanup: list[str]
  restore: list[str]
  setup_guide: list[str]


class Messages(TypedDict):
  usage: str
  no_configs: str
  setup_guide: str
  create: str
  created: str
  command_failure: str
  color_warning: str
  color_success: str
  color_reset: str


class Statuses(TypedDict):
  usage: int
  snapper_missing: int
  presence_missing: int
  presence_available: int
  command_failure: int


class Values(TypedDict):
  csv_header_rows: int
  config_column: int
  snapshot_class: str
  cleanup_type: str
  unknown_version: str


class Settings(TypedDict):
  actions: Actions
  commands: Commands
  messages: Messages
  statuses: Statuses
  values: Values


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid snapshot configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid snapshot configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid snapshot configuration: {label} must be an integer")
  return value


def _command(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
    raise TypeError(f"invalid snapshot configuration: {label} must be a non-empty string list")
  return list(value)


def settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/snapshot.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  actions = _mapping(config.get("actions"), "actions")
  commands = _mapping(config.get("commands"), "commands")
  messages = _mapping(config.get("messages"), "messages")
  statuses = _mapping(config.get("statuses"), "statuses")
  values = _mapping(config.get("values"), "values")
  return {
    "actions": {
      "create": _text(actions.get("create"), "actions.create"),
      "restore": _text(actions.get("restore"), "actions.restore"),
    },
    "commands": {
      "command_presence": _command(commands.get("command_presence"), "commands.command_presence"),
      "version": _command(commands.get("version"), "commands.version"),
      "list_configs": _command(commands.get("list_configs"), "commands.list_configs"),
      "create": _command(commands.get("create"), "commands.create"),
      "cleanup": _command(commands.get("cleanup"), "commands.cleanup"),
      "restore": _command(commands.get("restore"), "commands.restore"),
      "setup_guide": _command(commands.get("setup_guide"), "commands.setup_guide"),
    },
    "messages": {
      "usage": _text(messages.get("usage"), "messages.usage"),
      "no_configs": _text(messages.get("no_configs"), "messages.no_configs"),
      "setup_guide": _text(messages.get("setup_guide"), "messages.setup_guide"),
      "create": _text(messages.get("create"), "messages.create"),
      "created": _text(messages.get("created"), "messages.created"),
      "command_failure": _text(messages.get("command_failure"), "messages.command_failure"),
      "color_warning": _text(messages.get("color_warning"), "messages.color_warning"),
      "color_success": _text(messages.get("color_success"), "messages.color_success"),
      "color_reset": _text(messages.get("color_reset"), "messages.color_reset"),
    },
    "statuses": {
      "usage": _integer(statuses.get("usage"), "statuses.usage"),
      "snapper_missing": _integer(statuses.get("snapper_missing"), "statuses.snapper_missing"),
      "presence_missing": _integer(statuses.get("presence_missing"), "statuses.presence_missing"),
      "presence_available": _integer(statuses.get("presence_available"), "statuses.presence_available"),
      "command_failure": _integer(statuses.get("command_failure"), "statuses.command_failure"),
    },
    "values": {
      "csv_header_rows": _integer(values.get("csv_header_rows"), "values.csv_header_rows"),
      "config_column": _integer(values.get("config_column"), "values.config_column"),
      "snapshot_class": _text(values.get("snapshot_class"), "values.snapshot_class"),
      "cleanup_type": _text(values.get("cleanup_type"), "values.cleanup_type"),
      "unknown_version": _text(values.get("unknown_version"), "values.unknown_version"),
    },
  }


def run(config: Settings, command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
  try:
    return subprocess.run(command, check=False, text=True, capture_output=capture)
  except OSError as error:
    detail = error.strerror or str(error)
    print(config["messages"]["command_failure"].format(command=command[0], error=detail), file=sys.stderr)
    return subprocess.CompletedProcess(command, config["statuses"]["command_failure"], "", "")


def create(config: Settings) -> int:
  presence = run(config, config["commands"]["command_presence"])
  if presence.returncode == config["statuses"]["presence_missing"]:
    return config["statuses"]["snapper_missing"]
  if presence.returncode != config["statuses"]["presence_available"]:
    return presence.returncode

  description = run(config, config["commands"]["version"], capture=True)
  version = (description.stdout or "").strip() if description.returncode == 0 else ""
  if not version:
    version = config["values"]["unknown_version"]

  listed = run(config, config["commands"]["list_configs"], capture=True)
  if listed.returncode != 0:
    if listed.stderr:
      sys.stderr.write(listed.stderr)
    return listed.returncode
  rows = list(csv.reader((listed.stdout or "").splitlines()))
  names = [
    row[config["values"]["config_column"]]
    for row in rows[config["values"]["csv_header_rows"]:]
    if len(row) > config["values"]["config_column"] and row[config["values"]["config_column"]]
  ]
  if not names:
    print(
      f"{config['messages']['color_warning']}{config['messages']['no_configs']}{config['messages']['color_reset']}",
      file=sys.stderr,
    )
    root = Path(os.environ["AP"])
    guide = [argument.replace("{ap}", str(root)) for argument in config["commands"]["setup_guide"]]
    print(config["messages"]["setup_guide"].format(command=shlex.join(guide)), file=sys.stderr)
    return config["statuses"]["usage"]

  print(
    f"{config['messages']['color_success']}{config['messages']['create']}{config['messages']['color_reset']}"
  )
  for name in names:
    created = run(config, [
      *config["commands"]["create"], "-c", name, "create", "-c",
      str(config["values"]["snapshot_class"]), "-d", version,
    ])
    if created.returncode != 0:
      return created.returncode
    cleaned = run(config, [
      *config["commands"]["cleanup"], "-c", name, "cleanup",
      str(config["values"]["cleanup_type"]),
    ])
    if cleaned.returncode != 0:
      return cleaned.returncode

  print(config["messages"]["created"])
  return 0


def main(arguments: list[str] | None = None) -> int:
  try:
    config = settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  args = sys.argv[1:] if arguments is None else arguments
  if not args:
    print(config["messages"]["usage"], file=sys.stderr)
    return config["statuses"]["usage"]
  if args[0] == config["actions"]["create"]:
    return create(config)
  if args[0] == config["actions"]["restore"]:
    return run(config, config["commands"]["restore"]).returncode
  print(config["messages"]["usage"], file=sys.stderr)
  return config["statuses"]["usage"]


if __name__ == "__main__":
  raise SystemExit(main())
