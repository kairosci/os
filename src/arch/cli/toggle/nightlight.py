from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict, cast

import yaml
from arch.cli.lib.bounded import run_bounded


class Settings(TypedDict):
  commands: dict[str, list[str]]
  process_name: str
  actions: dict[str, str]
  identity_temperature: int
  night_temperature: int
  day_temperature: int
  startup_age_seconds: int
  temperature_pattern: str
  process_id_pattern: str
  maximum_temperature_output_bytes: int
  maximum_process_output_bytes: int
  read_chunk_bytes: int
  command_timeout_seconds: int
  cleanup_timeout_seconds: int
  startup_retry_interval_seconds: float
  startup_timeout_seconds: float
  maximum_startup_attempts: int
  messages: dict[str, str]
  statuses: dict[str, int]


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(f"{label} must be a string-keyed mapping")
  return cast(dict[str, object], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(f"{label} must be non-empty text")
  return value


def _integer(value: object, label: str, minimum: int = 1) -> int:
  if type(value) is not int or value < minimum:
    raise ValueError(f"{label} must be an integer no lower than {minimum}")
  return value


def _duration(value: object, label: str) -> float:
  if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
    raise ValueError(f"{label} must be a positive duration")
  return float(value)


def _settings() -> Settings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/nightlight.yml").read_text(encoding="utf-8"))
  document = _mapping(raw, "configuration")
  command_values = _mapping(document.get("commands"), "commands")
  values = _mapping(document.get("values"), "values")
  limits = _mapping(document.get("limits"), "limits")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  process_name = _text(values.get("process_name"), "values.process_name")
  command_names = ("temperature", "newest_process", "process_age", "start", "refresh_shell", "sleep")
  commands: dict[str, list[str]] = {}
  for name in command_names:
    command = command_values.get(name)
    if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
      raise ValueError(f"commands.{name} must be a non-empty argument vector")
    commands[name] = [item.format(process_name=process_name) for item in cast(list[str], command)]

  status_codes: dict[str, int] = {}
  for name in ("success", "invalid_arguments", "command_error"):
    status_codes[name] = _integer(statuses.get(name), f"statuses.{name}", 0)
    if status_codes[name] > 255:
      raise ValueError(f"statuses.{name} must be an exit status")

  temperature_pattern = _text(values.get("temperature_pattern"), "values.temperature_pattern")
  process_id_pattern = _text(values.get("process_id_pattern"), "values.process_id_pattern")
  re.compile(temperature_pattern)
  re.compile(process_id_pattern)
  actions = _mapping(values.get("actions"), "values.actions")
  return {
    "commands": commands,
    "process_name": process_name,
    "actions": {
      name: _text(actions.get(name), f"values.actions.{name}")
      for name in ("enable", "disable", "status")
    },
    "identity_temperature": _integer(values.get("identity_temperature"), "values.identity_temperature"),
    "night_temperature": _integer(values.get("night_temperature"), "values.night_temperature"),
    "day_temperature": _integer(values.get("day_temperature"), "values.day_temperature"),
    "startup_age_seconds": _integer(values.get("startup_age_seconds"), "values.startup_age_seconds", 0),
    "temperature_pattern": temperature_pattern,
    "process_id_pattern": process_id_pattern,
    "maximum_temperature_output_bytes": _integer(
      values.get("maximum_temperature_output_bytes"), "values.maximum_temperature_output_bytes"
    ),
    "maximum_process_output_bytes": _integer(
      values.get("maximum_process_output_bytes"), "values.maximum_process_output_bytes"
    ),
    "read_chunk_bytes": _integer(values.get("read_chunk_bytes"), "values.read_chunk_bytes"),
    "command_timeout_seconds": _integer(limits.get("command_timeout_seconds"), "limits.command_timeout_seconds"),
    "cleanup_timeout_seconds": _integer(limits.get("cleanup_timeout_seconds"), "limits.cleanup_timeout_seconds"),
    "startup_retry_interval_seconds": _duration(
      limits.get("startup_retry_interval_seconds"), "limits.startup_retry_interval_seconds"
    ),
    "startup_timeout_seconds": _duration(limits.get("startup_timeout_seconds"), "limits.startup_timeout_seconds"),
    "maximum_startup_attempts": _integer(
      limits.get("maximum_startup_attempts"), "limits.maximum_startup_attempts"
    ),
    "messages": {
      name: _text(messages.get(name), f"messages.{name}")
      for name in ("usage", "command_error", "start_error")
    },
    "statuses": status_codes,
  }


def _run(command: list[str], settings: Settings, maximum_bytes: int | None = None) -> bytes | None:
  try:
    return run_bounded(
      command,
      timeout_seconds=settings["command_timeout_seconds"],
      cleanup_timeout_seconds=settings["cleanup_timeout_seconds"],
      max_output_bytes=maximum_bytes or settings["maximum_temperature_output_bytes"],
      read_chunk_bytes=settings["read_chunk_bytes"],
    )
  except OSError:
    return None


def _temperature(settings: Settings) -> int | None:
  output = _run(settings["commands"]["temperature"], settings)
  if output is None:
    return None
  try:
    decoded = output.decode("utf-8", errors="strict")
  except UnicodeError:
    return None
  match = re.search(settings["temperature_pattern"], decoded)
  return int(match.group()) if match is not None else None


def _status(settings: Settings) -> int:
  temperature = _temperature(settings)
  print(json.dumps({
    "enabled": temperature is not None and temperature < settings["identity_temperature"],
    "temperature": temperature,
  }, separators=(",", ":")))
  return settings["statuses"]["success"]


def _process_age(settings: Settings) -> int | None:
  newest = _run([*settings["commands"]["newest_process"], settings["process_name"]], settings)
  if newest is None:
    return None
  try:
    newest_id = newest.decode("ascii", errors="strict").splitlines()[0].strip()
  except (UnicodeError, IndexError):
    return None
  if re.fullmatch(settings["process_id_pattern"], newest_id) is None:
    return None
  age = _run(
    [*settings["commands"]["process_age"], newest_id],
    settings,
    maximum_bytes=settings["maximum_process_output_bytes"],
  )
  if age is None:
    return None
  try:
    return int(age.decode("ascii", errors="strict").strip())
  except (ValueError, UnicodeError):
    return None


def _start(settings: Settings) -> bool:
  try:
    subprocess.Popen(
      settings["commands"]["start"],
      stdin=subprocess.DEVNULL,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      start_new_session=True,
      close_fds=True,
    )
  except OSError:
    return False
  return True


def _set_temperature(target: int, settings: Settings) -> bool:
  output = _run([*settings["commands"]["temperature"], str(target)], settings)
  return output is not None


def _wait_for_temperature(target: int, settings: Settings, deadline: float) -> bool:
  remaining = deadline - time.monotonic()
  if remaining <= 0:
    return False
  interval = min(settings["startup_retry_interval_seconds"], remaining)
  result = _run([*settings["commands"]["sleep"], str(interval)], settings)
  return result is not None and _temperature(settings) == target


def _change(enabled: bool, settings: Settings) -> int:
  temperature = _temperature(settings)
  if temperature is None:
    temperature = settings["day_temperature"]
  target = settings["night_temperature"] if enabled else settings["day_temperature"]
  if temperature == target:
    return settings["statuses"]["success"]

  process_age = _process_age(settings)
  if process_age is None:
    if not _start(settings):
      print(settings["messages"]["start_error"], file=sys.stderr)
      return settings["statuses"]["command_error"]
    wait_for_start = True
  else:
    wait_for_start = process_age < settings["startup_age_seconds"]

  deadline = time.monotonic() + settings["startup_timeout_seconds"]
  for attempt in range(settings["maximum_startup_attempts"]):
    if not _set_temperature(target, settings):
      print(settings["messages"]["command_error"], file=sys.stderr)
      return settings["statuses"]["command_error"]
    if not wait_for_start and _temperature(settings) == target:
      break
    if attempt + 1 == settings["maximum_startup_attempts"] or time.monotonic() >= deadline:
      break
    if _wait_for_temperature(target, settings, deadline):
      break

  if _temperature(settings) != target:
    print(settings["messages"]["command_error"], file=sys.stderr)
    return settings["statuses"]["command_error"]
  _run(settings["commands"]["refresh_shell"], settings)
  return settings["statuses"]["success"]


def nightlight_main(arguments: list[str]) -> int:
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError) as error:
    print(error, file=sys.stderr)
    return os.EX_CONFIG

  if arguments == [settings["actions"]["status"]]:
    return _status(settings)
  if len(arguments) > 1 or (arguments and arguments[0] not in (settings["actions"]["enable"], settings["actions"]["disable"])):
    print(settings["messages"]["usage"], file=sys.stderr)
    return settings["statuses"]["invalid_arguments"]
  if arguments:
    enabled = arguments[0] == settings["actions"]["enable"]
  else:
    temperature = _temperature(settings)
    enabled = temperature is None or temperature >= settings["identity_temperature"]
  return _change(enabled, settings)
