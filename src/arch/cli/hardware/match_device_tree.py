from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import TypedDict

import yaml


class Source(TypedDict):
  environment: str
  default: str
  suffix: str


class Settings(TypedDict):
  root_uid: int
  image_root_environment: str
  maximum_bytes: int
  sources: list[Source]
  statuses: dict[str, int]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid device tree configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"invalid device tree configuration: {label} must be a non-empty string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError(f"invalid device tree configuration: {label} must be a non-negative integer")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load(
    (root / "data/cli/hardware-match-device-tree.yml").read_text(encoding="utf-8")
  )
  document = _mapping(raw, "root")
  raw_sources = document.get("sources")
  if not isinstance(raw_sources, list) or not raw_sources:
    raise ValueError("invalid device tree configuration: sources must be a non-empty list")
  sources: list[Source] = []
  for index, raw_source in enumerate(raw_sources):
    source = _mapping(raw_source, f"sources[{index}]")
    sources.append({
      "environment": _text(source.get("environment"), f"sources[{index}].environment"),
      "default": _text(source.get("default"), f"sources[{index}].default"),
      "suffix": _text(source.get("suffix"), f"sources[{index}].suffix"),
    })
  raw_statuses = _mapping(document.get("statuses"), "statuses")
  return {
    "root_uid": _integer(document.get("root_uid"), "root_uid"),
    "image_root_environment": _text(document.get("image_root_environment"), "image_root_environment"),
    "maximum_bytes": _integer(document.get("maximum_bytes"), "maximum_bytes"),
    "sources": sources,
    "statuses": {
      "found": _integer(raw_statuses.get("found"), "statuses.found"),
      "not_found": _integer(raw_statuses.get("not_found"), "statuses.not_found"),
    },
  }


def _source_paths(settings: Settings) -> list[Path]:
  sources = settings["sources"]
  roots = [os.environ.get(source["environment"], "") for source in sources]
  image_root = os.environ.get(settings["image_root_environment"], "")
  use_fixtures = os.geteuid() != settings["root_uid"] and bool("".join((*roots, image_root)))
  if use_fixtures:
    return [
      Path(root) / source["suffix"]
      for source, root in zip(sources, roots, strict=True)
      if root
    ]
  return [Path(source["default"]) for source in sources]


def _compatible_strings(path: Path, maximum_bytes: int) -> list[bytes]:
  try:
    with path.open("rb") as stream:
      contents = stream.read(maximum_bytes + 1)
  except OSError:
    return []
  if len(contents) > maximum_bytes or not contents:
    return []
  entries = contents.split(b"\0")
  if entries[-1] == b"":
    entries.pop()
  return entries


def match_device_tree_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
    source = next((path for path in _source_paths(settings) if os.access(path, os.R_OK)), None)
    if source is None:
      return settings["statuses"]["not_found"]
    entries = _compatible_strings(source, settings["maximum_bytes"])
    wanted = [os.fsencode(value).lower() for value in arguments]
    found = any(entry.lower() in wanted for entry in entries)
    return settings["statuses"]["found"] if found else settings["statuses"]["not_found"]
  except (KeyError, OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG
