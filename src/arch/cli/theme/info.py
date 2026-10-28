from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Literal, TypedDict

import yaml


class Paths(TypedDict):
  state_home_environment: str
  state_home_default: str
  theme_name_file: str
  user_themes: str
  bundled_themes: str
  current_background: str
  user_backgrounds: str
  theme_backgrounds: str
  background_root: str


class CycleCommands(TypedDict):
  set_background: list[str]
  translate: list[str]
  notify: list[str]


class BackgroundCycle(TypedDict):
  extensions: list[str]
  commands: CycleCommands
  no_background_message: str
  notification_timeout_option: str
  notification_timeout: int


class BackgroundSetCommands(TypedDict):
  shell: list[str]


class BackgroundSet(TypedDict):
  commands: BackgroundSetCommands
  temporary_directory_prefix: str
  temporary_symlink_name: str


class BackgroundName(TypedDict):
  extension_pattern: str
  numeric_prefix_pattern: str
  word_initial_pattern: str
  hyphen: str
  separator: str


class ThemeName(TypedDict):
  pattern: str
  prefix_group: int
  uppercase_group: int
  hyphen: str
  separator: str


class MessageCatalog(TypedDict):
  default_language: str
  supported_languages: list[str]
  all_locale_environment: str
  locale_environment: str
  fallback_environment: str
  locale_separators: list[str]
  usage: dict[str, str]
  background_set_usage: dict[str, str]
  background_file_missing: dict[str, str]
  unknown: dict[str, str]


class Settings(TypedDict):
  paths: Paths
  background_cycle: BackgroundCycle
  background_set: BackgroundSet
  background_name: BackgroundName
  theme_name: ThemeName
  theme_id_pattern: str
  messages: MessageCatalog


class ResolvedPaths(TypedDict):
  theme_name_file: Path
  user_themes: Path
  bundled_themes: Path
  current_background: Path
  theme_backgrounds: Path
  background_root: Path


MessageKey = Literal["usage", "background_set_usage", "background_file_missing", "unknown"]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid theme command configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid theme command configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid theme command configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list):
    raise TypeError(f"invalid theme command configuration: {label} must be a list")
  return [_text(item, f"{label} item") for item in value]


def _language_map(value: object, label: str) -> dict[str, str]:
  raw = _mapping(value, label)
  return {_text(key, f"{label} language"): _text(item, f"{label} message") for key, item in raw.items()}


def _pattern(value: object, label: str) -> str:
  pattern = _text(value, label)
  try:
    re.compile(pattern)
  except re.error as error:
    raise ValueError(f"invalid theme command configuration: {label} is not a valid pattern") from error
  return pattern


def _settings() -> Settings:
  root = Path(os.environ["ARCH_PATH"])
  raw: object = yaml.safe_load((root / "data/cli/theme-info.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  paths = _mapping(settings.get("paths"), "paths")
  cycle = _mapping(settings.get("background_cycle"), "background_cycle")
  cycle_commands = _mapping(cycle.get("commands"), "background_cycle.commands")
  background_set = _mapping(settings.get("background_set"), "background_set")
  set_commands = _mapping(background_set.get("commands"), "background_set.commands")
  background_name = _mapping(settings.get("background_name"), "background_name")
  theme_name = _mapping(settings.get("theme_name"), "theme_name")
  messages = _mapping(settings.get("messages"), "messages")
  for key in ("usage", "background_set_usage", "background_file_missing", "unknown"):
    _language_map(messages.get(key), f"messages.{key}")
  default_language = _text(messages.get("default_language"), "messages.default_language")
  display_pattern = _pattern(theme_name.get("pattern"), "theme_name.pattern")
  prefix_group = _integer(theme_name.get("prefix_group"), "theme_name.prefix_group")
  uppercase_group = _integer(theme_name.get("uppercase_group"), "theme_name.uppercase_group")
  group_count = re.compile(display_pattern).groups
  if not 0 <= prefix_group <= group_count or not 0 <= uppercase_group <= group_count:
    raise ValueError("invalid theme command configuration: theme_name group index is outside the pattern")
  return {
    "paths": {
      "state_home_environment": _text(paths.get("state_home_environment"), "paths.state_home_environment"),
      "state_home_default": _text(paths.get("state_home_default"), "paths.state_home_default"),
      "theme_name_file": _text(paths.get("theme_name_file"), "paths.theme_name_file"),
      "user_themes": _text(paths.get("user_themes"), "paths.user_themes"),
      "bundled_themes": _text(paths.get("bundled_themes"), "paths.bundled_themes"),
      "current_background": _text(paths.get("current_background"), "paths.current_background"),
      "user_backgrounds": _text(paths.get("user_backgrounds"), "paths.user_backgrounds"),
      "theme_backgrounds": _text(paths.get("theme_backgrounds"), "paths.theme_backgrounds"),
      "background_root": _text(paths.get("background_root"), "paths.background_root"),
    },
    "background_cycle": {
      "extensions": _text_list(cycle.get("extensions"), "background_cycle.extensions"),
      "commands": {
        "set_background": _text_list(cycle_commands.get("set_background"), "background_cycle.commands.set_background"),
        "translate": _text_list(cycle_commands.get("translate"), "background_cycle.commands.translate"),
        "notify": _text_list(cycle_commands.get("notify"), "background_cycle.commands.notify"),
      },
      "no_background_message": _text(cycle.get("no_background_message"), "background_cycle.no_background_message"),
      "notification_timeout_option": _text(cycle.get("notification_timeout_option"), "background_cycle.notification_timeout_option"),
      "notification_timeout": _integer(cycle.get("notification_timeout"), "background_cycle.notification_timeout"),
    },
    "background_set": {
      "commands": {"shell": _text_list(set_commands.get("shell"), "background_set.commands.shell")},
      "temporary_directory_prefix": _text(background_set.get("temporary_directory_prefix"), "background_set.temporary_directory_prefix"),
      "temporary_symlink_name": _text(background_set.get("temporary_symlink_name"), "background_set.temporary_symlink_name"),
    },
    "background_name": {
      "extension_pattern": _pattern(background_name.get("extension_pattern"), "background_name.extension_pattern"),
      "numeric_prefix_pattern": _pattern(background_name.get("numeric_prefix_pattern"), "background_name.numeric_prefix_pattern"),
      "word_initial_pattern": _pattern(background_name.get("word_initial_pattern"), "background_name.word_initial_pattern"),
      "hyphen": _text(background_name.get("hyphen"), "background_name.hyphen"),
      "separator": _text(background_name.get("separator"), "background_name.separator"),
    },
    "theme_name": {
      "pattern": display_pattern,
      "prefix_group": prefix_group,
      "uppercase_group": uppercase_group,
      "hyphen": _text(theme_name.get("hyphen"), "theme_name.hyphen"),
      "separator": _text(theme_name.get("separator"), "theme_name.separator"),
    },
    "theme_id_pattern": _pattern(settings.get("theme_id_pattern"), "theme_id_pattern"),
    "messages": {
      "default_language": default_language,
      "supported_languages": _text_list(messages.get("supported_languages"), "messages.supported_languages"),
      "all_locale_environment": _text(messages.get("all_locale_environment"), "messages.all_locale_environment"),
      "locale_environment": _text(messages.get("locale_environment"), "messages.locale_environment"),
      "fallback_environment": _text(messages.get("fallback_environment"), "messages.fallback_environment"),
      "locale_separators": _text_list(messages.get("locale_separators"), "messages.locale_separators"),
      "usage": _language_map(messages.get("usage"), "messages.usage"),
      "background_set_usage": _language_map(messages.get("background_set_usage"), "messages.background_set_usage"),
      "background_file_missing": _language_map(messages.get("background_file_missing"), "messages.background_file_missing"),
      "unknown": _language_map(messages.get("unknown"), "messages.unknown"),
    },
  }


def _path(value: str, **values: str) -> Path:
  return Path(value.format(**values))


def _paths(settings: Settings) -> ResolvedPaths:
  home = str(Path.home())
  ap = os.environ["ARCH_PATH"]
  paths = settings["paths"]
  state_home = os.environ.get(paths["state_home_environment"])
  if state_home is None or state_home == "":
    state_home = paths["state_home_default"].format(home=home)
  values = {"home": home, "arch_path": ap, "state_home": state_home}
  return {
    "theme_name_file": _path(paths["theme_name_file"], **values),
    "user_themes": _path(paths["user_themes"], **values),
    "bundled_themes": _path(paths["bundled_themes"], **values),
    "current_background": _path(paths["current_background"], **values),
    "theme_backgrounds": _path(paths["theme_backgrounds"], **values),
    "background_root": _path(paths["background_root"], **values),
  }


def _language(settings: Settings) -> str:
  messages = settings["messages"]
  configured = (
    os.environ.get(messages["all_locale_environment"])
    or os.environ.get(messages["locale_environment"])
    or os.environ.get(messages["fallback_environment"])
  )
  language = configured or messages["default_language"]
  for separator in messages["locale_separators"]:
    language = language.split(separator, maxsplit=1)[0]
  language = language.lower()
  if language in messages["supported_languages"]:
    return language
  return messages["default_language"]


def _message(settings: Settings, key: MessageKey) -> str:
  messages = settings["messages"]
  language = _language(settings)
  localized = messages[key]
  return localized.get(language, localized[messages["default_language"]])


def _theme_current_main() -> int:
  settings = _settings()
  theme_name_file = _paths(settings)["theme_name_file"]
  if not theme_name_file.is_file():
    print(_message(settings, "unknown"))
    return 0
  name = theme_name_file.read_text(encoding="utf-8").strip()
  display = settings["theme_name"]
  name = re.sub(
    display["pattern"],
    lambda match: match.group(display["prefix_group"]) + match.group(display["uppercase_group"]).upper(),
    name,
  )
  print(name.replace(display["hyphen"], display["separator"]))
  return 0


def _theme_dir_main(arguments: list[str]) -> int:
  settings = _settings()
  if not arguments or not re.fullmatch(settings["theme_id_pattern"], arguments[0]):
    print(_message(settings, "usage"), file=sys.stderr)
    return 1
  paths = _paths(settings)
  user_theme = paths["user_themes"] / arguments[0]
  if user_theme.is_dir():
    print(user_theme)
  else:
    print(paths["bundled_themes"] / arguments[0])
  return 0


def _theme_list_main() -> int:
  settings = _settings()
  paths = _paths(settings)
  names: set[str] = set()
  for path, include_symlinks in ((paths["user_themes"], True), (paths["bundled_themes"], False)):
    try:
      children = path.iterdir()
      for child in children:
        if (child.is_symlink() and include_symlinks) or (child.is_dir() and (include_symlinks or not child.is_symlink())):
          names.add(child.name)
    except OSError:
      continue
  display = settings["theme_name"]
  for name in sorted(names):
    name = re.sub(
      display["pattern"],
      lambda match: match.group(display["prefix_group"]) + match.group(display["uppercase_group"]).upper(),
      name,
    )
    print(name.replace(display["hyphen"], display["separator"]))
  return 0


def _background_current_main() -> int:
  settings = _settings()
  background_link = _paths(settings)["current_background"]
  if not background_link.is_symlink():
    print(_message(settings, "unknown"))
    return 0
  name = Path(os.path.realpath(background_link)).name
  display = settings["background_name"]
  name = re.sub(display["extension_pattern"], "", name)
  name = re.sub(display["numeric_prefix_pattern"], "", name, count=1)
  name = name.replace(display["hyphen"], display["separator"])
  name = re.sub(display["word_initial_pattern"], lambda match: match.group(1).upper(), name)
  print(name)
  return 0


def _background_next_main() -> int:
  settings = _settings()
  paths = _paths(settings)
  theme_name_file = paths["background_root"]
  try:
    theme_name = theme_name_file.read_text(encoding="utf-8").strip()
  except OSError:
    theme_name = ""
  values = {
    "home": str(Path.home()),
    "state_home": str(paths["current_background"].parents[2]),
    "theme": theme_name,
  }
  directories: list[Path] = []
  if re.fullmatch(settings["theme_id_pattern"], theme_name):
    directories.append(Path(settings["paths"]["user_backgrounds"].format(**values)))
  directories.append(Path(settings["paths"]["theme_backgrounds"].format(**values)))
  extensions = {extension.casefold() for extension in settings["background_cycle"]["extensions"]}
  backgrounds: list[Path] = []
  for directory in directories:
    try:
      backgrounds.extend(
        entry for entry in directory.iterdir()
        if entry.is_file() and entry.suffix.casefold() in extensions
      )
    except OSError:
      continue
  backgrounds.sort(key=str)

  commands = settings["background_cycle"]["commands"]
  if not backgrounds:
    translated = subprocess.run(
      [*commands["translate"], settings["background_cycle"]["no_background_message"]],
      check=False,
      capture_output=True,
      text=True,
    )
    notification = subprocess.run(
      [
        *commands["notify"],
        translated.stdout.strip(),
        settings["background_cycle"]["notification_timeout_option"],
        str(settings["background_cycle"]["notification_timeout"]),
      ],
      check=False,
    )
    return notification.returncode

  try:
    current = os.readlink(paths["current_background"])
  except OSError:
    current = ""
  background_names = [str(background) for background in backgrounds]
  try:
    current_index = background_names.index(current)
  except ValueError:
    current_index = -1
  next_index = (current_index + 1) % len(backgrounds) if current_index >= 0 else 0
  result = subprocess.run([*commands["set_background"], background_names[next_index]], check=False)
  return result.returncode


def _background_set_main(arguments: list[str]) -> int:
  settings = _settings()
  if not arguments:
    print(_message(settings, "background_set_usage"), file=sys.stderr)
    return 1
  background = Path(arguments[0]).resolve()
  if not background.is_file():
    message = _message(settings, "background_file_missing").format(path=background)
    print(message, file=sys.stderr)
    return 1

  link = _paths(settings)["current_background"]
  link.parent.mkdir(parents=True, exist_ok=True)
  temporary_directory = Path(
    tempfile.mkdtemp(
      prefix=settings["background_set"]["temporary_directory_prefix"],
      dir=link.parent,
    )
  )
  try:
    temporary_link = temporary_directory / settings["background_set"]["temporary_symlink_name"]
    temporary_link.symlink_to(background)
    os.replace(temporary_link, link)
  finally:
    temporary_directory.rmdir()

  result = subprocess.run(
    [*settings["background_set"]["commands"]["shell"], str(background)],
    check=False,
  )
  return result.returncode


def _entry(operation: Callable[[], int], label: str) -> int:
  try:
    return operation()
  except (KeyError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load or apply {label} settings: {error}", file=sys.stderr)
    return os.EX_CONFIG
  except OSError as error:
    print(f"Could not access files for {label}: {error}", file=sys.stderr)
    return os.EX_SOFTWARE
  except subprocess.SubprocessError as error:
    print(f"Could not run {label} command: {error}", file=sys.stderr)
    return os.EX_SOFTWARE


def theme_current_main() -> int:
  return _entry(_theme_current_main, "theme")


def theme_dir_main(arguments: list[str]) -> int:
  return _entry(lambda: _theme_dir_main(arguments), "theme directory")


def theme_list_main() -> int:
  return _entry(_theme_list_main, "theme list")


def background_current_main() -> int:
  return _entry(_background_current_main, "background")


def background_next_main() -> int:
  return _entry(_background_next_main, "background cycle")


def background_set_main(arguments: list[str]) -> int:
  return _entry(lambda: _background_set_main(arguments), "background selection")
