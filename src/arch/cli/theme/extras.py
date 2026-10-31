from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

import yaml


def _mapping(value: object, label: str) -> Mapping[str, object]:
  if not isinstance(value, Mapping):
    raise TypeError(f"invalid theme extras configuration: {label} must be a mapping")
  return value


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid theme extras configuration: {label} must be a non-empty string")
  return value


def _status(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid theme extras configuration: {label} must be an integer")
  return value


def main() -> int:
  try:
    root = Path(os.environ["AP"])
    config = _mapping(
      yaml.safe_load((root / "data/cli/theme-extras.yml").read_text(encoding="utf-8")),
      "root",
    )
    paths = _mapping(config.get("paths"), "paths")
    output = _mapping(config.get("output"), "output")
    statuses = _mapping(config.get("status"), "status")
    themes_path = Path(_text(paths.get("themes"), "paths.themes"))
    marker = _text(paths.get("git_marker"), "paths.git_marker")
    separator = _text(output.get("separator"), "output.separator")
    trailing_newline = output.get("trailing_newline")
    listed_status = _status(statuses.get("listed"), "status.listed")
    none_status = _status(statuses.get("none"), "status.none")
    if themes_path.is_absolute() or ".." in themes_path.parts or Path(marker).name != marker:
      raise ValueError("invalid theme extras configuration: paths must stay within their roots")
    if not isinstance(trailing_newline, bool):
      raise TypeError("invalid theme extras configuration: output.trailing_newline must be boolean")
    themes_root = Path.home() / themes_path
    try:
      themes = sorted(
        (
          theme
          for theme in themes_root.iterdir()
          if not theme.is_symlink() and theme.is_dir() and (theme / marker).is_dir()
        ),
        key=lambda theme: os.fsencode(theme.name),
      )
    except (FileNotFoundError, NotADirectoryError, PermissionError):
      themes = []
    if not themes:
      return none_status
    result = separator.join(str(theme) for theme in themes)
    if trailing_newline:
      result += separator
    sys.stdout.write(result)
    return listed_status
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load theme extras configuration: {error}", file=sys.stderr)
    return 2
