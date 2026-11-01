from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class Settings(TypedDict):
  commands: dict[str, list[str]]
  paths: dict[str, str]
  command_timeout: int
  delay: int
  usage: str
  configuration_error: str
  operation_error: str
  resetting: str
  done: str
  reloading_module: str
  invalid_device_name: str
  success: int
  invalid_arguments: int
  operation_failed: int
  not_found: int


def _mapping(value: object, label: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise TypeError(f"Trackpad restart {label} must be a mapping")
  return cast(dict[str, object], value)


def _strings(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
    raise TypeError(f"Trackpad restart {label} must be a non-empty string list")
  return cast(list[str], value)


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"Trackpad restart {label} must be a non-empty string")
  return value


def _integer(value: object, label: str) -> int:
  if type(value) is not int or value < 1:
    raise TypeError(f"Trackpad restart {label} must be a positive integer")
  return value


def _status(value: object, label: str) -> int:
  if type(value) is not int or not 0 <= value <= 255:
    raise TypeError(f"Trackpad restart {label} must be an exit status")
  return value


def _settings(document: dict[str, object]) -> Settings:
  commands = _mapping(document.get("commands"), "commands")
  paths = _mapping(document.get("paths"), "paths")
  limits = _mapping(document.get("limits"), "limits")
  messages = _mapping(document.get("messages"), "messages")
  statuses = _mapping(document.get("statuses"), "statuses")
  device_name_pattern = _text(paths.get("device_name_pattern"), "device name pattern")
  re.compile(device_name_pattern)
  module = _text(paths.get("module"), "module name")
  if re.fullmatch(device_name_pattern, module) is None:
    raise TypeError("Trackpad restart module name is invalid")
  return {
    "commands": {
      name: _strings(commands.get(name), f"commands.{name}")
      for name in ("module_list", "module_match", "sudo", "tee", "module_remove", "module_load", "delay")
    },
    "paths": {
      name: _text(paths.get(name), f"paths.{name}")
      for name in ("driver", "devices", "device_name_pattern", "unbind", "bind", "module")
    },
    "command_timeout": _integer(limits.get("command_timeout_seconds"), "command timeout"),
    "delay": _integer(limits.get("rebind_delay_seconds"), "rebind delay"),
    "usage": _text(messages.get("usage"), "usage message"),
    "configuration_error": _text(messages.get("configuration_error"), "configuration error message"),
    "operation_error": _text(messages.get("operation_error"), "operation error message"),
    "resetting": _text(messages.get("resetting"), "reset message"),
    "done": _text(messages.get("done"), "completion message"),
    "reloading_module": _text(messages.get("reloading_module"), "module message"),
    "invalid_device_name": _text(messages.get("invalid_device_name"), "invalid device message"),
    "success": _status(statuses.get("success"), "success status"),
    "invalid_arguments": _status(statuses.get("invalid_arguments"), "argument status"),
    "operation_failed": _status(statuses.get("operation_failed"), "operation status"),
    "not_found": _status(statuses.get("not_found"), "not-found status"),
  }


def _run(
  command: list[str],
  settings: Settings,
  *,
  input_data: str | None = None,
  capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    command,
    check=False,
    input=input_data,
    text=True,
    stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
    timeout=settings["command_timeout"],
  )


def _reset_device(device: Path, settings: Settings) -> int:
  paths = settings["paths"]
  device_name = device.name
  if re.fullmatch(paths["device_name_pattern"], device_name) is None:
    raise ValueError(settings["invalid_device_name"])
  print(settings["resetting"].format(device=device_name), flush=True)
  for operation in ("unbind", "bind"):
    target = paths[operation]
    result = _run(
      [*settings["commands"]["sudo"], *settings["commands"]["tee"], target],
      settings,
      input_data=f"{device_name}\n",
    )
    if result.returncode != settings["success"]:
      return settings["operation_failed"]
    if operation == "unbind":
      _run([*settings["commands"]["delay"], str(settings["delay"])], settings)
  print(settings["done"], flush=True)
  return settings["success"]


def main(arguments: list[str]) -> int:
  configuration_error = ""
  try:
    root = Path(os.environ["AP"])
    raw_messages = yaml.safe_load((root / "data/cli/restart-trackpad.yml").read_text(encoding="utf-8"))
    messages = _mapping(_mapping(raw_messages, "configuration").get("messages"), "messages")
    configuration_error = _text(messages.get("configuration_error"), "configuration error message")
    settings = _settings(_mapping(raw_messages, "configuration"))
  except (KeyError, OSError, re.error, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    if configuration_error:
      print(configuration_error.format(error=error), file=sys.stderr)
    else:
      print(error, file=sys.stderr)
    return 1
  if arguments:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]

  paths = settings["paths"]
  try:
    driver = Path(paths["driver"])
    for device in sorted(driver.glob(paths["devices"])):
      if not device.exists():
        continue
      status = _reset_device(device, settings)
      if status != settings["success"]:
        return status

    modules = _run(settings["commands"]["module_list"], settings, capture_output=True)
    if modules.returncode != settings["success"] or modules.stdout is None:
      return settings["operation_failed"]
    present = _run(
      [*settings["commands"]["module_match"], paths["module"]],
      settings,
      input_data=modules.stdout,
    )
    if present.returncode == settings["success"]:
      print(settings["reloading_module"].format(module=paths["module"]), flush=True)
      for command in (
        [*settings["commands"]["sudo"], *settings["commands"]["module_remove"], paths["module"]],
        [*settings["commands"]["sudo"], *settings["commands"]["module_load"], paths["module"]],
      ):
        result = _run(command, settings)
        if result.returncode != settings["success"]:
          return settings["operation_failed"]
    elif present.returncode != settings["not_found"]:
      return settings["operation_failed"]
  except (OSError, subprocess.SubprocessError, ValueError) as error:
    print(settings["operation_error"].format(error=error), file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]
