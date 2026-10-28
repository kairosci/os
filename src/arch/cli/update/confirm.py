from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import NotRequired, TypedDict

import yaml


class Commands(TypedDict):
  i18n: list[str]
  style: list[str]
  confirm: list[str]


class MessageLine(TypedDict):
  message: str
  prefix: NotRequired[str]
  arguments: NotRequired[list[str]]


class TextLine(TypedDict):
  text: str


StyleLine = MessageLine | TextLine


class Style(TypedDict):
  lines: list[StyleLine]


class Flags(TypedDict):
  affirmative: str
  negative: str


class Messages(TypedDict):
  yes: str
  no: str
  continue_: str
  cancelled: str


class Statuses(TypedDict):
  confirmed: int
  cancelled: int
  failed: int


class ConfirmConfig(TypedDict):
  commands: Commands
  style: Style
  flags: Flags
  messages: Messages
  strings: dict[str, str]
  statuses: Statuses


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid update confirmation configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid update confirmation configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid update confirmation configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid update confirmation configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _text_mapping(value: object, label: str) -> dict[str, str]:
  mapping = _mapping(value, label)
  return {
    _text(key, f"{label} key"): _text(item, f"{label} value")
    for key, item in mapping.items()
  }


def _style_lines(value: object) -> list[StyleLine]:
  if not isinstance(value, list):
    raise ValueError("invalid update confirmation configuration: style.lines must be a list")
  lines: list[StyleLine] = []
  for index, raw_line in enumerate(value):
    line = _mapping(raw_line, f"style.lines[{index}]")
    if "message" in line and "text" not in line:
      message_line: MessageLine = {"message": _text(line.get("message"), f"style.lines[{index}].message")}
      if "prefix" in line:
        message_line["prefix"] = _text(line.get("prefix"), f"style.lines[{index}].prefix")
      if "arguments" in line:
        message_line["arguments"] = _text_list(line.get("arguments"), f"style.lines[{index}].arguments")
      lines.append(message_line)
    elif "text" in line and "message" not in line:
      lines.append({"text": _text(line.get("text"), f"style.lines[{index}].text")})
    else:
      raise ValueError(f"invalid update confirmation configuration: style.lines[{index}] needs message or text")
  return lines


def load_config() -> ConfirmConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/update-confirm.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  commands = _mapping(config.get("commands"), "commands")
  style = _mapping(config.get("style"), "style")
  flags = _mapping(config.get("flags"), "flags")
  messages = _mapping(config.get("messages"), "messages")
  statuses = _mapping(config.get("statuses"), "statuses")
  return {
    "commands": {
      "i18n": _text_list(commands.get("i18n"), "commands.i18n"),
      "style": _text_list(commands.get("style"), "commands.style"),
      "confirm": _text_list(commands.get("confirm"), "commands.confirm"),
    },
    "style": {"lines": _style_lines(style.get("lines"))},
    "flags": {
      "affirmative": _text(flags.get("affirmative"), "flags.affirmative"),
      "negative": _text(flags.get("negative"), "flags.negative"),
    },
    "messages": {
      "yes": _text(messages.get("yes"), "messages.yes"),
      "no": _text(messages.get("no"), "messages.no"),
      "continue_": _text(messages.get("continue"), "messages.continue"),
      "cancelled": _text(messages.get("cancelled"), "messages.cancelled"),
    },
    "strings": _text_mapping(config.get("strings"), "strings"),
    "statuses": {
      "confirmed": _integer(statuses.get("confirmed"), "statuses.confirmed"),
      "cancelled": _integer(statuses.get("cancelled"), "statuses.cancelled"),
      "failed": _integer(statuses.get("failed"), "statuses.failed"),
    },
  }


def localized(config: ConfirmConfig, key: str, *arguments: str) -> str:
  result = subprocess.run(
    [*config["commands"]["i18n"], key, *arguments],
    check=False,
    capture_output=True,
    text=True,
  )
  return result.stdout.rstrip("\n")


def main() -> int:
  try:
    config = load_config()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load update confirmation configuration: {error}", file=sys.stderr)
    return 2
  try:
    lines: list[str] = []
    for item in config["style"]["lines"]:
      if "message" in item:
        key = config["strings"][_text(item.get("message"), "style line message")]
        arguments = _text_list(item.get("arguments", []), "style line arguments")
        prefix = _text(item.get("prefix", ""), "style line prefix")
        message = localized(config, key, *arguments)
        lines.append(f"{prefix}{message}")
      else:
        lines.append(_text(item.get("text"), "style line text"))
    subprocess.run([*config["commands"]["style"], *lines], check=False)
    print()

    affirmative = localized(config, config["messages"]["yes"])
    negative = localized(config, config["messages"]["no"])
    question = localized(config, config["messages"]["continue_"])
    result = subprocess.run(
      [
        *config["commands"]["confirm"],
        config["flags"]["affirmative"], affirmative,
        config["flags"]["negative"], negative,
        question,
      ],
      check=False,
    )
    if result.returncode != config["statuses"]["confirmed"]:
      print(localized(config, config["messages"]["cancelled"]))
      return config["statuses"]["cancelled"]
    return config["statuses"]["confirmed"]
  except (KeyError, OSError, subprocess.SubprocessError, TypeError, ValueError) as error:
    print(f"Could not confirm update: {error}", file=sys.stderr)
    return config["statuses"]["failed"]


if __name__ == "__main__":
  raise SystemExit(main())
