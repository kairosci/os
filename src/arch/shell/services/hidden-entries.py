#!/usr/bin/python3 -I

from __future__ import annotations

import os
from pathlib import Path
import re
import sys
from typing import Any

import yaml


def settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/shell/hidden-entries.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError
  return config


def application_directories(config: dict[str, Any]) -> list[Path]:
  paths = config["paths"]
  home = str(Path.home())
  directories = [Path(paths["user_applications"].format(home=home))]
  data_dirs = os.environ.get(paths["system_data_dirs_environment"]) or paths["system_data_dirs_default"]
  if isinstance(data_dirs, str):
    data_dirs = data_dirs.split(paths["system_data_dirs_separator"])
  directories.extend(
    Path(data_dir) / paths["applications_directory"]
    for data_dir in data_dirs
    if data_dir
  )
  directories.append(Path(paths["nix_applications"].format(home=home)))
  return directories


def desktop_matches(value: str, desktop_names: set[str], separator: str) -> bool:
  return any(part and part in desktop_names for part in value.split(separator))


def is_hidden_desktop_file(path: Path, desktop_names: set[str], config: dict[str, Any]) -> bool:
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


def desktop_id(path: Path, root: Path, config: dict[str, Any]) -> str:
  entry = config["desktop_entry"]
  relative = path.relative_to(root).as_posix()
  if relative.endswith(entry["extension"]):
    relative = relative[: -len(entry["extension"])]
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
  config = settings()
  desktop_entry = config["desktop_entry"]
  desktop_names = set()
  if len(sys.argv) > 1:
    desktop_names = {
      name
      for name in sys.argv[1].split(desktop_entry["desktop_names_separator"])
      if name
    }
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
