from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict, cast

import yaml


class FileAction(TypedDict):
  path: str
  command: list[str]


class ProcessAction(TypedDict):
  name: str
  signal: str


class Settings(TypedDict):
  files: list[FileAction]
  processes: list[ProcessAction]
  process_probe: list[str]
  process_reload: list[str]
  command_timeout: int
  operation_timeout: int
  usage_message: str
  configuration_error: str
  operation_error: str
  success: int
  invalid_arguments: int
  operation_failed: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"Terminal restart {label} must be a mapping")
  return cast(dict[str, object], value)


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
    raise TypeError(f"Terminal restart {label} must be a non-empty string list")
  return cast(list[str], value)


def _text(value: object) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError("Terminal restart messages must be non-empty strings")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 1:
    raise TypeError(f"Terminal restart {label} must be a positive integer")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"Terminal restart {label} must be an exit status")
  return value


def _settings(document: dict[str, object]) -> Settings:
  raw_files = document.get("files")
  raw_processes = document.get("processes")
  if not isinstance(raw_files, list) or not isinstance(raw_processes, list):
    raise TypeError("Terminal restart files and processes must be lists")
  files: list[FileAction] = []
  for item in raw_files:
    values = _mapping(item, "file action")
    path = _text(values.get("path"))
    command = _strings(values.get("command"), "file command")
    files.append({"path": path, "command": command})
  processes: list[ProcessAction] = []
  for item in raw_processes:
    values = _mapping(item, "process action")
    name = _text(values.get("name"))
    signal = _text(values.get("signal"))
    if not name.isascii() or not name.replace("-", "").replace("_", "").isalnum():
      raise TypeError("Terminal restart process names must be ASCII identifiers")
    if not signal.isascii() or not signal.isalnum():
      raise TypeError("Terminal restart signals must be ASCII identifiers")
    processes.append({"name": name, "signal": signal})
  commands = _mapping(document.get("commands"), "commands")
  limits = _mapping(document.get("limits"), "limits")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  return {
    "files": files,
    "processes": processes,
    "process_probe": _strings(commands.get("process_probe"), "process probe"),
    "process_reload": _strings(commands.get("process_reload"), "process reload"),
    "command_timeout": _integer(limits.get("command_timeout_seconds"), "command timeout"),
    "operation_timeout": _integer(limits.get("operation_timeout_seconds"), "operation timeout"),
    "usage_message": _text(messages.get("usage")),
    "configuration_error": _text(messages.get("configuration_error")),
    "operation_error": _text(messages.get("operation_error")),
    "success": _status(statuses.get("success"), "success status"),
    "invalid_arguments": _status(statuses.get("invalid_arguments"), "argument status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
  }


def main(arguments: list[str]) -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw: object = yaml.safe_load((root / "data/cli/restart-terminal.yml").read_text(encoding="utf-8"))
    document = _mapping(raw, "configuration")
    messages = _mapping(document.get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"))
    settings = _settings(document)
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    if configuration_error:
      print(configuration_error.format(error=error), file=sys.stderr)
    else:
      print(error, file=sys.stderr)
    return 1
  if arguments:
    print(settings["usage_message"], file=sys.stderr)
    return settings["invalid_arguments"]

  home = Path.home()
  deadline = time.monotonic() + settings["operation_timeout"]
  try:
    for action in settings["files"]:
      path = home / action["path"]
      if path.is_file():
        _run([part.replace("{path}", str(path)) for part in action["command"]], settings, deadline)
    for process in settings["processes"]:
      probe = [part.replace("{process}", process["name"]) for part in settings["process_probe"]]
      result = _run(probe, settings, deadline)
      if result.returncode != settings["success"]:
        continue
      reload = [
        part.replace("{process}", process["name"]).replace("{signal}", process["signal"])
        for part in settings["process_reload"]
      ]
      _run(reload, settings, deadline)
  except (OSError, subprocess.SubprocessError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]


def _run(command: list[str], settings: Settings, deadline: float) -> subprocess.CompletedProcess[bytes]:
  remaining = deadline - time.monotonic()
  if remaining <= 0:
    raise subprocess.TimeoutExpired(command, settings["operation_timeout"])
  return subprocess.run(
    command,
    check=False,
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    timeout=min(settings["command_timeout"], remaining),
  )
