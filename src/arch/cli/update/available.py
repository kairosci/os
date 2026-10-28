from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import TypedDict

import yaml


class Commands(TypedDict):
  checkupdates: list[str]
  i18n: list[str]


class Checkout(TypedDict):
  system_path: str
  git: list[str]
  upstream_args: list[str]
  fetch_args: list[str]
  fetch_timeout_seconds: int
  behind_args: list[str]


class Messages(TypedDict):
  up_to_date: str
  checkout: str


class Statuses(TypedDict):
  updates_available: int
  no_updates: int
  failed: int


class UpdateConfig(TypedDict):
  commands: Commands
  checkout: Checkout
  messages: Messages
  statuses: Statuses


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid update availability configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid update availability configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid update availability configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid update availability configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def load_config() -> UpdateConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/update-available.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  commands = _mapping(config.get("commands"), "commands")
  checkout = _mapping(config.get("checkout"), "checkout")
  messages = _mapping(config.get("messages"), "messages")
  statuses = _mapping(config.get("statuses"), "statuses")
  return {
    "commands": {
      "checkupdates": _text_list(commands.get("checkupdates"), "commands.checkupdates"),
      "i18n": _text_list(commands.get("i18n"), "commands.i18n"),
    },
    "checkout": {
      "system_path": _text(checkout.get("system_path"), "checkout.system_path"),
      "git": _text_list(checkout.get("git"), "checkout.git"),
      "upstream_args": _text_list(checkout.get("upstream_args"), "checkout.upstream_args"),
      "fetch_args": _text_list(checkout.get("fetch_args"), "checkout.fetch_args"),
      "fetch_timeout_seconds": _integer(
        checkout.get("fetch_timeout_seconds"), "checkout.fetch_timeout_seconds"
      ),
      "behind_args": _text_list(checkout.get("behind_args"), "checkout.behind_args"),
    },
    "messages": {
      "up_to_date": _text(messages.get("up_to_date"), "messages.up_to_date"),
      "checkout": _text(messages.get("checkout"), "messages.checkout"),
    },
    "statuses": {
      "updates_available": _integer(statuses.get("updates_available"), "statuses.updates_available"),
      "no_updates": _integer(statuses.get("no_updates"), "statuses.no_updates"),
      "failed": _integer(statuses.get("failed"), "statuses.failed"),
    },
  }


def run(command: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
  return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def checkout_updates(config: UpdateConfig, ap: str) -> list[str]:
  checkout = config["checkout"]
  if ap == checkout["system_path"]:
    return []

  upstream_result = run([*checkout["git"], "-C", ap, *checkout["upstream_args"]])
  upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else ""
  if not upstream:
    return []

  try:
    run(
      [*checkout["git"], "-C", ap, *checkout["fetch_args"]],
      timeout=int(checkout["fetch_timeout_seconds"]),
    )
    behind_result = run(
      [*checkout["git"], "-C", ap, *checkout["behind_args"], upstream]
    )
  except (OSError, subprocess.TimeoutExpired):
    return []

  try:
    behind = int(behind_result.stdout.strip()) if behind_result.returncode == 0 else 0
  except ValueError:
    behind = 0
  if behind <= 0:
    return []

  message = run([
    *config["commands"]["i18n"], "--count", str(behind),
    config["messages"]["checkout"], str(behind), upstream,
  ])
  return [message.stdout.rstrip("\n")]


def main() -> int:
  try:
    config = load_config()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load update availability configuration: {error}", file=sys.stderr)
    return 2

  try:
    updates = checkout_updates(config, os.environ["AP"])
    result = run(config["commands"]["checkupdates"])
    if result.returncode == config["statuses"]["updates_available"]:
      updates.extend(line for line in result.stdout.splitlines() if line.strip())

    if updates:
      print("\n".join(updates))
      return int(config["statuses"]["updates_available"])

    localized = run([*config["commands"]["i18n"], config["messages"]["up_to_date"]])
    print(localized.stdout.rstrip("\n"))
    return config["statuses"]["no_updates"]
  except (KeyError, OSError, TypeError, ValueError, subprocess.TimeoutExpired) as error:
    print(f"Could not check for updates: {error}", file=sys.stderr)
    return config["statuses"]["failed"]


if __name__ == "__main__":
  raise SystemExit(main())
