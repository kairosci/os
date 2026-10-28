from __future__ import annotations

import locale
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

import yaml


class Commands(TypedDict):
  current: list[str]
  list: list[str]


class CurrentOptions(TypedDict):
  family_separator: str
  family_index: int


class ListOptions(TypedDict):
  exclude_pattern: str


class Configure(TypedDict):
  python: str
  script: str
  arguments: list[str]


class CjkMessages(TypedDict):
  default_language: str
  usage: dict[str, str]


class ExitCodes(TypedDict):
  usage: int


class CjkOptions(TypedDict):
  config_home_environment: str
  config_home_default: str
  preference_path: str
  preference_pattern: str
  preference_group: int
  default_variant: str
  variants: list[str]
  help_arguments: list[str]
  exit_codes: ExitCodes
  messages: CjkMessages
  configure: Configure
  restart_command: list[str]
  i18n_command: list[str]
  changed_message: str
  restart_apps_message: str
  notification_command: list[str]
  notification_glyph: str


class Settings(TypedDict):
  commands: Commands
  current: CurrentOptions
  list: ListOptions
  cjk: CjkOptions


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid font command configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid font command configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid font command configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value:
    raise TypeError(f"invalid font command configuration: {label} must be a non-empty list")
  return [_text(item, f"{label} item") for item in value]


def _pattern(value: object, label: str) -> str:
  pattern = _text(value, label)
  try:
    re.compile(pattern)
  except re.error as error:
    raise ValueError(f"invalid font command configuration: {label} is not a valid pattern") from error
  return pattern


def _language_map(value: object, label: str) -> dict[str, str]:
  raw = _mapping(value, label)
  return {_text(key, f"{label} key"): _text(message, f"{label} value") for key, message in raw.items()}


def _settings() -> Settings:
  root = Path(os.environ["ARCH_PATH"])
  raw: object = yaml.safe_load((root / "data/cli/fonts.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  commands = _mapping(settings.get("commands"), "commands")
  current = _mapping(settings.get("current"), "current")
  listing = _mapping(settings.get("list"), "list")
  cjk = _mapping(settings.get("cjk"), "cjk")
  configure = _mapping(cjk.get("configure"), "cjk.configure")
  exits = _mapping(cjk.get("exit_codes"), "cjk.exit_codes")
  messages = _mapping(cjk.get("messages"), "cjk.messages")
  usage = _language_map(messages.get("usage"), "cjk.messages.usage")
  language = _text(messages.get("default_language"), "cjk.messages.default_language")
  preference_pattern = _pattern(cjk.get("preference_pattern"), "cjk.preference_pattern")
  preference_group = _integer(cjk.get("preference_group"), "cjk.preference_group")
  if not 0 <= preference_group <= re.compile(preference_pattern).groups:
    raise ValueError("invalid font command configuration: CJK preference group is outside the pattern")
  return {
    "commands": {
      "current": _text_list(commands.get("current"), "commands.current"),
      "list": _text_list(commands.get("list"), "commands.list"),
    },
    "current": {
      "family_separator": _text(current.get("family_separator"), "current.family_separator"),
      "family_index": _integer(current.get("family_index"), "current.family_index"),
    },
    "list": {"exclude_pattern": _pattern(listing.get("exclude_pattern"), "list.exclude_pattern")},
    "cjk": {
      "config_home_environment": _text(cjk.get("config_home_environment"), "cjk.config_home_environment"),
      "config_home_default": _text(cjk.get("config_home_default"), "cjk.config_home_default"),
      "preference_path": _text(cjk.get("preference_path"), "cjk.preference_path"),
      "preference_pattern": preference_pattern,
      "preference_group": preference_group,
      "default_variant": _text(cjk.get("default_variant"), "cjk.default_variant"),
      "variants": _text_list(cjk.get("variants"), "cjk.variants"),
      "help_arguments": _text_list(cjk.get("help_arguments"), "cjk.help_arguments"),
      "exit_codes": {"usage": _integer(exits.get("usage"), "cjk.exit_codes.usage")},
      "messages": {"default_language": language, "usage": usage},
      "configure": {
        "python": _text(configure.get("python"), "cjk.configure.python"),
        "script": _text(configure.get("script"), "cjk.configure.script"),
        "arguments": _text_list(configure.get("arguments"), "cjk.configure.arguments"),
      },
      "restart_command": _text_list(cjk.get("restart_command"), "cjk.restart_command"),
      "i18n_command": _text_list(cjk.get("i18n_command"), "cjk.i18n_command"),
      "changed_message": _text(cjk.get("changed_message"), "cjk.changed_message"),
      "restart_apps_message": _text(cjk.get("restart_apps_message"), "cjk.restart_apps_message"),
      "notification_command": _text_list(cjk.get("notification_command"), "cjk.notification_command"),
      "notification_glyph": _text(cjk.get("notification_glyph"), "cjk.notification_glyph"),
    },
  }


def _current_main() -> int:
  settings = _settings()
  result = subprocess.run(settings["commands"]["current"], check=False, stdout=subprocess.PIPE, text=True)
  lines = result.stdout.splitlines()
  first = lines[0] if lines else ""
  separator = settings["current"]["family_separator"]
  index = settings["current"]["family_index"]
  fields = first.split(separator)
  if len(fields) > index:
    print(fields[index])
  return 0


def _list_main() -> int:
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


def _cjk_main(arguments: list[str]) -> int:
  settings = _settings()
  options = settings["cjk"]
  if not arguments:
    config_home = os.environ.get(options["config_home_environment"])
    if config_home is None or config_home == "":
      config_home = str(Path.home() / options["config_home_default"])
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
  language = os.environ.get("LANG", options["messages"]["default_language"]).split(".", 1)[0].split("_", 1)[0]
  usage = options["messages"]["usage"]
  if variant in options["help_arguments"]:
    print(usage.get(language, usage[options["messages"]["default_language"]]))
    return 0
  if variant not in options["variants"] or len(arguments) != 1:
    print(usage.get(language, usage[options["messages"]["default_language"]]), file=sys.stderr)
    return options["exit_codes"]["usage"]

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


def _entry(operation: Callable[[], int], label: str) -> int:
  try:
    return operation()
  except (TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Invalid {label} configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  except (locale.Error, OSError, UnicodeError, subprocess.SubprocessError) as error:
    print(f"Could not run {label}: {error}", file=sys.stderr)
    return os.EX_SOFTWARE


def current_main() -> int:
  return _entry(_current_main, "font current")


def list_main() -> int:
  return _entry(_list_main, "font list")


def cjk_main(arguments: list[str]) -> int:
  return _entry(lambda: _cjk_main(arguments), "CJK font")


if __name__ == "__main__":
  command = sys.argv[1] if len(sys.argv) > 1 else ""
  if command == "current":
    raise SystemExit(current_main())
  if command == "list":
    raise SystemExit(list_main())
  if command == "cjk":
    raise SystemExit(cjk_main(sys.argv[2:]))
  raise SystemExit(2)
