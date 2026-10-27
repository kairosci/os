from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/theme-info.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError
  return settings


def _path(value: str, **values: str) -> Path:
  return Path(value.format(**values))


def _paths(settings: dict[str, Any]) -> dict[str, Path]:
  home = str(Path.home())
  arch_path = os.environ["ARCH_PATH"]
  state_home = os.environ.get(settings["paths"]["state_home_environment"])
  if not state_home:
    state_home = settings["paths"]["state_home_default"].format(home=home)
  values = {"home": home, "arch_path": arch_path, "state_home": state_home}
  return {
    name: _path(value, **values)
    for name, value in settings["paths"].items()
    if name not in ("state_home_environment", "state_home_default", "user_backgrounds")
  }


def _language(settings: dict[str, Any]) -> str:
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


def _message(settings: dict[str, Any], key: str) -> str:
  messages = settings["messages"]
  language = _language(settings)
  return messages[key].get(language, messages[key][messages["default_language"]])


def theme_current_main() -> int:
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


def theme_dir_main(arguments: list[str]) -> int:
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


def theme_list_main() -> int:
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


def background_current_main() -> int:
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


def background_next_main() -> int:
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
  directories = []
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


def background_set_main(arguments: list[str]) -> int:
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
