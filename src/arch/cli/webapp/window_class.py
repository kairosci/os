from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TypedDict, cast
from urllib.parse import urlsplit

import yaml


class WindowClassSettings(TypedDict):
  input_scheme: str
  scheme_separator: str
  empty_path: str
  path_separator: str
  path_replacement: str
  output_template: str


class Settings(TypedDict):
  window_class: WindowClassSettings
  messages: dict[str, str]
  statuses: dict[str, int]


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"invalid web app window class configuration: {label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"invalid web app window class configuration: {label} must be non-empty text")
  return value


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load(
    (root / "data/cli/webapp-window-class.yml").read_text(encoding="utf-8")
  )
  document = _mapping(raw, "root")
  raw_window_class = _mapping(document.get("window_class"), "window_class")
  raw_messages = _mapping(document.get("messages"), "messages")
  raw_statuses = _mapping(document.get("statuses"), "statuses")
  window_class: WindowClassSettings = {
    "input_scheme": _text(raw_window_class.get("input_scheme"), "window_class.input_scheme"),
    "scheme_separator": _text(raw_window_class.get("scheme_separator"), "window_class.scheme_separator"),
    "empty_path": _text(raw_window_class.get("empty_path"), "window_class.empty_path"),
    "path_separator": _text(raw_window_class.get("path_separator"), "window_class.path_separator"),
    "path_replacement": _text(raw_window_class.get("path_replacement"), "window_class.path_replacement"),
    "output_template": _text(raw_window_class.get("output_template"), "window_class.output_template"),
  }
  if not window_class["output_template"].count("{host}") == 1:
    raise ValueError("invalid web app window class configuration: output template needs one host placeholder")
  if not window_class["output_template"].count("{path}") == 1:
    raise ValueError("invalid web app window class configuration: output template needs one path placeholder")
  messages = {key: _text(value, f"messages.{key}") for key, value in raw_messages.items()}
  if set(messages) != {"usage"}:
    raise ValueError("invalid web app window class configuration: messages must define usage")
  statuses = {
    key: value
    for key, value in raw_statuses.items()
    if type(value) is int and 0 <= value <= 255
  }
  if set(statuses) != {"success", "invalid_arguments"}:
    raise ValueError("invalid web app window class configuration: statuses are incomplete")
  return {"window_class": window_class, "messages": messages, "statuses": statuses}


def window_class(url: str, settings: Settings) -> str:
  configured = settings["window_class"]
  address = urlsplit(
    url if configured["scheme_separator"] in url else f"{configured['input_scheme']}{configured['scheme_separator']}{url}"
  )
  host = (address.hostname or "").lower()
  path = (address.path or configured["empty_path"]).replace(
    configured["path_separator"], configured["path_replacement"]
  )
  return configured["output_template"].format(host=host, path=path)


def main(arguments: list[str] | None = None) -> int:
  settings = _settings()
  arguments = sys.argv[1:] if arguments is None else arguments
  if len(arguments) != 1:
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]
  try:
    result = window_class(arguments[0], settings)
  except ValueError:
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]
  print(result)
  return settings["statuses"]["success"]
