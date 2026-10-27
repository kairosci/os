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

import yaml

LAST_STATUS = 0


def settings() -> dict:
  root = Path(os.environ["ARCH_PATH"])
  with (root / "data/shell/clipboard-capture.yml").open(encoding="utf-8") as stream:
    return yaml.safe_load(stream)


def bounded_command(command: list[str], config: dict, input_stream=None) -> bytes | None:
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


def bounded_stdin(config: dict) -> bytes | None:
  raw = bounded_command(["cat"], config, input_stream=sys.stdin.buffer)
  return raw if raw else None


def decode_text(raw: bytes, config: dict) -> str:
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


def emit_text(raw: bytes, config: dict) -> None:
  if not raw:
    return
  capture = config["capture"]
  entry = {capture["json_type_key"]: capture["text_entry_type"], capture["json_text_key"]: decode_text(raw, config)}
  print(json.dumps(entry, ensure_ascii=False, separators=(",", ":")))


def capture_timestamp(config: dict) -> str:
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


def emit_image(mime: str, raw: bytes, state_dir: Path, config: dict) -> None:
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
  types = type_output.decode(errors="replace").splitlines() if type_output else []
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
