#!/usr/bin/python3 -I
"""Capture clipboard text and images as JSON history entries."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import BinaryIO, TypedDict, TypeGuard

import yaml

LAST_STATUS = 0


class ClipboardPaths(TypedDict):
  state_directory: str
  image_directory: str
  temporary_prefix: str
  user_cache_environment: str
  default_state_directory: str


class ClipboardCapture(TypedDict):
  timeout_command: str
  timeout_argument: str
  sensitive_environment: str
  sensitive_value: str
  sensitive_mime: str
  list_types_arguments: list[str]
  text_arguments: list[str]
  mime_arguments: list[str]
  text_type_prefix: str
  generic_text_types: list[str]
  image_types: list[str]
  image_mime_prefix: str
  jpeg_extension: str
  jpeg_replacement: str
  image_entry_type: str
  text_entry_type: str
  json_mime_key: str
  json_type_key: str
  json_path_key: str
  json_capture_time_key: str
  json_text_key: str
  captured_at_format: str
  timestamp_locale_command: str
  timestamp_locale_argument: str
  date_command: str


class Utf16Settings(TypedDict):
  byte_order_mark_little_endian: str
  byte_order_mark_big_endian: str
  minimum_padding_numerator: int
  padding_denominator: int
  maximum_opposite_padding_numerator: int
  control_ranges: list[list[int]]
  fallback_encoding: str


class ClipboardSettings(TypedDict):
  paths: ClipboardPaths
  capture: ClipboardCapture
  utf16: Utf16Settings


def _is_string_list(value: object) -> TypeGuard[list[str]]:
  return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_clipboard_settings(value: object) -> TypeGuard[ClipboardSettings]:
  if not isinstance(value, dict):
    return False
  paths = value.get("paths")
  capture = value.get("capture")
  utf16 = value.get("utf16")
  if not isinstance(paths, dict) or not isinstance(capture, dict) or not isinstance(utf16, dict):
    return False
  path_fields = (
    "state_directory", "image_directory", "temporary_prefix", "user_cache_environment", "default_state_directory",
  )
  capture_fields = (
    "timeout_command", "timeout_argument", "sensitive_environment", "sensitive_value", "sensitive_mime",
    "text_type_prefix", "image_mime_prefix", "jpeg_extension", "jpeg_replacement", "image_entry_type",
    "text_entry_type", "json_mime_key", "json_type_key", "json_path_key", "json_capture_time_key",
    "json_text_key", "captured_at_format", "timestamp_locale_command", "timestamp_locale_argument", "date_command",
  )
  string_lists = (
    "list_types_arguments", "text_arguments", "mime_arguments", "generic_text_types", "image_types",
  )
  control_ranges = utf16.get("control_ranges")
  return (
    all(isinstance(paths.get(key), str) for key in path_fields)
    and all(isinstance(capture.get(key), str) for key in capture_fields)
    and all(_is_string_list(capture.get(key)) for key in string_lists)
    and isinstance(utf16.get("byte_order_mark_little_endian"), str)
    and isinstance(utf16.get("byte_order_mark_big_endian"), str)
    and type(utf16.get("minimum_padding_numerator")) is int
    and type(utf16.get("padding_denominator")) is int
    and type(utf16.get("maximum_opposite_padding_numerator")) is int
    and isinstance(control_ranges, list)
    and all(
      isinstance(bounds, list) and len(bounds) == 2 and all(type(bound) is int for bound in bounds)
      for bounds in control_ranges
    )
    and isinstance(utf16.get("fallback_encoding"), str)
  )


def settings() -> ClipboardSettings:
  root = Path(os.environ["AP"])
  with (root / "data/shell/clipboard-capture.yml").open(encoding="utf-8") as stream:
    config: object = yaml.safe_load(stream)
  if not _is_clipboard_settings(config):
    raise ValueError("invalid clipboard capture settings")
  return config


def bounded_command(command: list[str], config: ClipboardSettings, input_stream: BinaryIO | None = None) -> bytes | None:
  global LAST_STATUS
  capture = config["capture"]
  invocation = [capture["timeout_command"], capture["timeout_argument"], *command]
  try:
    result = subprocess.run(
      invocation,
      stdin=input_stream,
      stdout=subprocess.PIPE,
      stderr=subprocess.DEVNULL,
      check=False,
    )
  except OSError:
    LAST_STATUS = 127
    return None
  LAST_STATUS = result.returncode
  return result.stdout if result.returncode == 0 else None


def bounded_stdin(config: ClipboardSettings) -> bytes | None:
  raw = bounded_command(["cat"], config, input_stream=sys.stdin.buffer)
  return raw if raw is not None and len(raw) > 0 else None


def decode_text(raw: bytes, config: ClipboardSettings) -> str:
  rules = config["utf16"]
  encoding = None
  heuristic = False
  little_bom = rules["byte_order_mark_little_endian"].encode("latin-1")
  big_bom = rules["byte_order_mark_big_endian"].encode("latin-1")
  if raw.startswith((little_bom, big_bom)):
    encoding = "utf-16"
  elif len(raw) % 2 == 0 and b"\0" in raw:
    units = len(raw) // 2
    nul_minimum = rules["minimum_padding_numerator"]
    denominator = rules["padding_denominator"]
    opposite_maximum = rules["maximum_opposite_padding_numerator"]
    even_nuls = raw[::2].count(0)
    odd_nuls = raw[1::2].count(0)
    if odd_nuls * denominator >= units * nul_minimum and even_nuls * denominator < units * opposite_maximum:
      encoding = "utf-16-le"
      heuristic = True
    elif even_nuls * denominator >= units * nul_minimum and odd_nuls * denominator < units * opposite_maximum:
      encoding = "utf-16-be"
      heuristic = True

  text = None
  if encoding:
    try:
      text = raw.decode(encoding, errors="strict")
    except UnicodeError:
      pass
  if heuristic and text is not None:
    if any(any(start <= ord(character) <= end for start, end in rules["control_ranges"]) for character in text):
      text = None
  if text is None:
    text = raw.decode(rules["fallback_encoding"], errors="replace")
  return text


def emit_text(raw: bytes, config: ClipboardSettings) -> None:
  if not raw:
    return
  capture = config["capture"]
  entry = {capture["json_type_key"]: capture["text_entry_type"], capture["json_text_key"]: decode_text(raw, config)}
  print(json.dumps(entry, ensure_ascii=False, separators=(",", ":")))


def capture_timestamp(config: ClipboardSettings) -> str:
  capture = config["capture"]
  environment = os.environ.copy()
  try:
    locale = subprocess.run(
      [capture["timestamp_locale_command"], capture["timestamp_locale_argument"]],
      stdout=subprocess.PIPE,
      stderr=subprocess.DEVNULL,
      text=True,
      check=False,
    ).stdout.strip()
    if locale:
      environment["LC_TIME"] = locale
  except OSError:
    pass
  try:
    return subprocess.run(
      [capture["date_command"], "+" + capture["captured_at_format"]],
      stdout=subprocess.PIPE,
      stderr=subprocess.DEVNULL,
      text=True,
      env=environment,
      check=False,
    ).stdout.strip()
  except OSError:
    return ""


def emit_image(mime: str, raw: bytes, state_dir: Path, config: ClipboardSettings) -> None:
  if not raw:
    return
  capture = config["capture"]
  extension = mime.removeprefix(capture["image_mime_prefix"])
  if extension == capture["jpeg_extension"]:
    extension = capture["jpeg_replacement"]

  image_dir = state_dir / config["paths"]["image_directory"]
  image_dir.mkdir(parents=True, exist_ok=True)
  digest = hashlib.sha256(raw).hexdigest()
  image_path = image_dir / (digest + "." + extension)
  if not image_path.exists():
    descriptor, temporary_name = tempfile.mkstemp(prefix=config["paths"]["temporary_prefix"], dir=image_dir)
    temporary = Path(temporary_name)
    try:
      with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
      try:
        os.link(temporary, image_path)
      except FileExistsError:
        pass
    finally:
      temporary.unlink(missing_ok=True)

  entry = {
    capture["json_type_key"]: capture["image_entry_type"],
    capture["json_mime_key"]: mime,
    capture["json_path_key"]: str(image_path),
    capture["json_capture_time_key"]: capture_timestamp(config),
  }
  print(json.dumps(entry, ensure_ascii=False, separators=(",", ":")))


def main() -> int:
  config = settings()
  paths = config["paths"]
  capture = config["capture"]
  state_root_value = os.environ.get(paths["user_cache_environment"]) or str(Path.home() / paths["default_state_directory"])
  state_root = Path(state_root_value)
  state_dir = state_root / paths["state_directory"]
  state_dir.mkdir(parents=True, exist_ok=True)

  type_output = bounded_command(["wl-paste", *capture["list_types_arguments"]], config)
  types = type_output.decode(errors="replace").splitlines() if type_output is not None else []
  if os.environ.get(capture["sensitive_environment"]) == capture["sensitive_value"] or capture["sensitive_mime"] in types:
    return 0

  mode = sys.argv[1] if len(sys.argv) > 1 else ""
  if mode == "text" or mode in capture["image_types"]:
    raw = bounded_stdin(config)
    if mode == "text":
      if raw is not None:
        emit_text(raw, config)
    elif raw is not None:
      emit_image(mode, raw, state_dir, config)
    return 0

  for mime in capture["image_types"]:
    if mime in types:
      raw = bounded_command(["wl-paste", *capture["mime_arguments"], mime], config)
      if raw is not None:
        emit_image(mime, raw, state_dir, config)
      return 0

  if any(item.startswith(capture["text_type_prefix"]) for item in types) or any(
    item in types for item in capture["generic_text_types"]
  ):
    raw = bounded_command(["wl-paste", *capture["text_arguments"]], config)
    if raw is not None:
      if not raw:
        return 1
      emit_text(raw, config)
      return 0
    return LAST_STATUS or 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
