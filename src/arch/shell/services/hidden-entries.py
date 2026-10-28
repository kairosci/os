#!/usr/bin/python3 -I

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import TypedDict

import yaml


class Paths(TypedDict):
  user_applications: str
  nix_applications: str
  system_data_dirs_environment: str
  system_data_dirs_default: list[str]
  system_data_dirs_separator: str
  applications_directory: str


class DesktopEntry(TypedDict):
  extension: str
  group: str
  section_pattern: str
  section_name_group: int
  hidden_keys: list[str]
  only_show_key: str
  not_show_key: str
  true_value: str
  id_path_separator: str
  id_name_separator: str
  key_value_separator: str
  line_endings: list[str]
  desktop_names_separator: str
  list_values_separator: str


class Settings(TypedDict):
  paths: Paths
  desktop_entry: DesktopEntry


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid hidden-entries configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid hidden-entries configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid hidden-entries configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list):
    raise TypeError(f"invalid hidden-entries configuration: {label} must be a list")
  return [_text(item, f"{label} item") for item in value]


def settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/shell/hidden-entries.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  paths = _mapping(config.get("paths"), "paths")
  entry = _mapping(config.get("desktop_entry"), "desktop_entry")
  default_dirs = paths.get("system_data_dirs_default")
  if isinstance(default_dirs, str):
    parsed_default_dirs = [_text(item, "paths.system_data_dirs_default item") for item in default_dirs.split(":")]
  else:
    parsed_default_dirs = _text_list(default_dirs, "paths.system_data_dirs_default")
  return {
    "paths": {
      "user_applications": _text(paths.get("user_applications"), "paths.user_applications"),
      "nix_applications": _text(paths.get("nix_applications"), "paths.nix_applications"),
      "system_data_dirs_environment": _text(paths.get("system_data_dirs_environment"), "paths.system_data_dirs_environment"),
      "system_data_dirs_default": parsed_default_dirs,
      "system_data_dirs_separator": _text(paths.get("system_data_dirs_separator"), "paths.system_data_dirs_separator"),
      "applications_directory": _text(paths.get("applications_directory"), "paths.applications_directory"),
    },
    "desktop_entry": {
      "extension": _text(entry.get("extension"), "desktop_entry.extension"),
      "group": _text(entry.get("group"), "desktop_entry.group"),
      "section_pattern": _text(entry.get("section_pattern"), "desktop_entry.section_pattern"),
      "section_name_group": _integer(entry.get("section_name_group"), "desktop_entry.section_name_group"),
      "hidden_keys": _text_list(entry.get("hidden_keys"), "desktop_entry.hidden_keys"),
      "only_show_key": _text(entry.get("only_show_key"), "desktop_entry.only_show_key"),
      "not_show_key": _text(entry.get("not_show_key"), "desktop_entry.not_show_key"),
      "true_value": _text(entry.get("true_value"), "desktop_entry.true_value"),
      "id_path_separator": _text(entry.get("id_path_separator"), "desktop_entry.id_path_separator"),
      "id_name_separator": _text(entry.get("id_name_separator"), "desktop_entry.id_name_separator"),
      "key_value_separator": _text(entry.get("key_value_separator"), "desktop_entry.key_value_separator"),
      "line_endings": _text_list(entry.get("line_endings"), "desktop_entry.line_endings"),
      "desktop_names_separator": _text(entry.get("desktop_names_separator"), "desktop_entry.desktop_names_separator"),
      "list_values_separator": _text(entry.get("list_values_separator"), "desktop_entry.list_values_separator"),
    },
  }


def application_directories(config: Settings) -> list[Path]:
  paths = config["paths"]
  home = str(Path.home())
  directories = [Path(paths["user_applications"].format(home=home))]
  data_dirs_value = os.environ.get(paths["system_data_dirs_environment"])
  data_dirs: list[str]
  if data_dirs_value is None or data_dirs_value == "":
    data_dirs = paths["system_data_dirs_default"]
  else:
    data_dirs = data_dirs_value.split(paths["system_data_dirs_separator"])
  directories.extend(
    Path(data_dir) / paths["applications_directory"]
    for data_dir in data_dirs
    if data_dir
  )
  directories.append(Path(paths["nix_applications"].format(home=home)))
  return directories


def desktop_matches(value: str, desktop_names: set[str], separator: str) -> bool:
  return any(part and part in desktop_names for part in value.split(separator))


def is_hidden_desktop_file(path: Path, desktop_names: set[str], config: Settings) -> bool:
  entry = config["desktop_entry"]
  in_desktop_entry = False
  hidden = False
  only_show_in = ""
  not_show_in = ""
  section_pattern = re.compile(entry["section_pattern"])

  try:
    with path.open(encoding="utf-8", errors="replace") as file:
      for raw_line in file:
        line = raw_line
        for ending in entry["line_endings"]:
          line = line.removesuffix(ending)
        section = section_pattern.fullmatch(line)
        if section:
          in_desktop_entry = section.group(entry["section_name_group"]) == entry["group"]
          continue
        separator = entry["key_value_separator"]
        if not in_desktop_entry or separator not in line:
          continue
        key, value = line.split(separator, maxsplit=1)
        if key in entry["hidden_keys"] and value == entry["true_value"]:
          hidden = True
        elif key == entry["only_show_key"]:
          only_show_in = value
        elif key == entry["not_show_key"]:
          not_show_in = value
  except OSError:
    return False

  separator = entry["list_values_separator"]
  if hidden:
    return True
  if only_show_in and not desktop_matches(only_show_in, desktop_names, separator):
    return True
  return bool(not_show_in and desktop_matches(not_show_in, desktop_names, separator))


def desktop_id(path: Path, root: Path, config: Settings) -> str:
  entry = config["desktop_entry"]
  relative = path.relative_to(root).as_posix()
  relative = relative.removesuffix(entry["extension"])
  return relative.replace(entry["id_path_separator"], entry["id_name_separator"])


def desktop_files(root: Path, extension: str) -> list[Path]:
  found: list[Path] = []
  if not root.is_dir() or root.is_symlink():
    return found
  for current, directories, files in os.walk(root, followlinks=False):
    directories.sort(key=os.fsencode)
    for name in files:
      if not name.endswith(extension):
        continue
      path = Path(current) / name
      if path.is_file() and not path.is_symlink():
        found.append(path)
  return sorted(found, key=lambda path: os.fsencode(path))


def main() -> int:
  try:
    config = settings()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load hidden-entries configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  desktop_entry = config["desktop_entry"]
  desktop_names: set[str] = set()
  if len(sys.argv) > 1:
    desktop_names = {name for name in sys.argv[1].split(desktop_entry["desktop_names_separator"]) if name}
  seen_ids: set[str] = set()

  for directory in application_directories(config):
    for path in desktop_files(directory, desktop_entry["extension"]):
      identifier = desktop_id(path, directory, config)
      if identifier in seen_ids:
        continue
      seen_ids.add(identifier)
      if is_hidden_desktop_file(path, desktop_names, config):
        print(identifier)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
