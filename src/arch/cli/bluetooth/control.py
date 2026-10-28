from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal, NotRequired, TypedDict

import yaml

RunCommandName = Literal["bluetoothctl", "rfkill", "timeout", "sleep", "power", "i18n"]


class Commands(TypedDict):
  bluetoothctl: list[str]
  rfkill: list[str]
  timeout: list[str]
  sleep: list[str]
  power: list[str]
  i18n: list[str]
  device: dict[str, list[str]]
  rfkill_actions: dict[str, list[str]]
  timeout_unit: str


class EnsurePower(TypedDict):
  command: RunCommandName
  arguments: list[str]
  ignore_failure: bool


class PoweredQuery(TypedDict):
  command: RunCommandName
  arguments: list[str]
  timeout: int | float
  success_text: str


class DeviceStep(TypedDict):
  command: str
  timeout: NotRequired[int | float]
  required: bool


class DeviceConfig(TypedDict):
  actions: list[str]
  address_pattern: str
  usage_key: str
  ensure_power: EnsurePower
  powered_query: PoweredQuery
  action_commands: dict[str, list[DeviceStep]]


class PowerTiming(TypedDict):
  wait_environment: str
  wait_default: int | float
  controller_query_timeout: int | float
  show_timeout: int | float
  power_timeout: int | float
  poll_interval: int | float


class PowerFields(TypedDict):
  controller_address: int
  powered_text: str


class PowerCommands(TypedDict):
  controller_list: list[str]
  controller_show: list[str]
  power_on: list[str]


class PowerConfig(TypedDict):
  actions: list[str]
  action_names: dict[str, str]
  usage_key: str
  failed_key: str
  timing: PowerTiming
  fields: PowerFields
  commands: PowerCommands


class BluetoothConfig(TypedDict):
  commands: Commands
  device: DeviceConfig
  power: PowerConfig


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid Bluetooth command configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid Bluetooth command configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid Bluetooth command configuration: {label} must be an integer")
  return value


def _number(value: object, label: str) -> int | float:
  if not isinstance(value, (int, float)) or isinstance(value, bool):
    raise TypeError(f"invalid Bluetooth command configuration: {label} must be numeric")
  return value


def _boolean(value: object, label: str) -> bool:
  if not isinstance(value, bool):
    raise TypeError(f"invalid Bluetooth command configuration: {label} must be a boolean")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise TypeError(f"invalid Bluetooth command configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _text_list_mapping(value: object, label: str) -> dict[str, list[str]]:
  mapping = _mapping(value, label)
  return {
    _text(key, f"{label} key"): _text_list(item, f"{label}.{key}")
    for key, item in mapping.items()
  }


def _text_mapping(value: object, label: str) -> dict[str, str]:
  mapping = _mapping(value, label)
  return {
    _text(key, f"{label} key"): _text(item, f"{label} value")
    for key, item in mapping.items()
  }


def _run_command_name(value: object, label: str) -> RunCommandName:
  name = _text(value, label)
  allowed: tuple[RunCommandName, ...] = ("bluetoothctl", "rfkill", "timeout", "sleep", "power", "i18n")
  if name not in allowed:
    raise ValueError(f"invalid Bluetooth command configuration: {label} has an unknown command")
  return name


def _device_steps(value: object) -> dict[str, list[DeviceStep]]:
  mapping = _mapping(value, "device.action_commands")
  actions: dict[str, list[DeviceStep]] = {}
  for action_value, raw_steps in mapping.items():
    action = _text(action_value, "device.action_commands key")
    if not isinstance(raw_steps, list):
      raise TypeError(f"invalid Bluetooth command configuration: device.action_commands.{action} must be a list")
    steps: list[DeviceStep] = []
    for index, raw_step in enumerate(raw_steps):
      step = _mapping(raw_step, f"device.action_commands.{action}[{index}]")
      parsed_step: DeviceStep = {
        "command": _text(step.get("command"), f"device.action_commands.{action}[{index}].command"),
        "required": _boolean(step.get("required"), f"device.action_commands.{action}[{index}].required"),
      }
      if "timeout" in step:
        parsed_step["timeout"] = _number(step.get("timeout"), f"device.action_commands.{action}[{index}].timeout")
      steps.append(parsed_step)
    actions[action] = steps
  return actions


def load_config() -> BluetoothConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/bluetooth.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  commands = _mapping(config.get("commands"), "commands")
  device_commands = _mapping(commands.get("device"), "commands.device")
  rfkill_actions = _mapping(commands.get("rfkill_actions"), "commands.rfkill_actions")
  device = _mapping(config.get("device"), "device")
  ensure_power = _mapping(device.get("ensure_power"), "device.ensure_power")
  powered_query = _mapping(device.get("powered_query"), "device.powered_query")
  power = _mapping(config.get("power"), "power")
  action_names = _mapping(power.get("action_names"), "power.action_names")
  timing = _mapping(power.get("timing"), "power.timing")
  fields = _mapping(power.get("fields"), "power.fields")
  power_commands = _mapping(power.get("commands"), "power.commands")
  return {
    "commands": {
      "bluetoothctl": _text_list(commands.get("bluetoothctl"), "commands.bluetoothctl"),
      "rfkill": _text_list(commands.get("rfkill"), "commands.rfkill"),
      "timeout": _text_list(commands.get("timeout"), "commands.timeout"),
      "sleep": _text_list(commands.get("sleep"), "commands.sleep"),
      "power": _text_list(commands.get("power"), "commands.power"),
      "i18n": _text_list(commands.get("i18n"), "commands.i18n"),
      "device": _text_list_mapping(device_commands, "commands.device"),
      "rfkill_actions": _text_list_mapping(rfkill_actions, "commands.rfkill_actions"),
      "timeout_unit": _text(commands.get("timeout_unit"), "commands.timeout_unit"),
    },
    "device": {
      "actions": _text_list(device.get("actions"), "device.actions"),
      "address_pattern": _text(device.get("address_pattern"), "device.address_pattern"),
      "usage_key": _text(device.get("usage_key"), "device.usage_key"),
      "ensure_power": {
        "command": _run_command_name(ensure_power.get("command"), "device.ensure_power.command"),
        "arguments": _text_list(ensure_power.get("arguments"), "device.ensure_power.arguments"),
        "ignore_failure": _boolean(ensure_power.get("ignore_failure"), "device.ensure_power.ignore_failure"),
      },
      "powered_query": {
        "command": _run_command_name(powered_query.get("command"), "device.powered_query.command"),
        "arguments": _text_list(powered_query.get("arguments"), "device.powered_query.arguments"),
        "timeout": _number(powered_query.get("timeout"), "device.powered_query.timeout"),
        "success_text": _text(powered_query.get("success_text"), "device.powered_query.success_text"),
      },
      "action_commands": _device_steps(device.get("action_commands")),
    },
    "power": {
      "actions": _text_list(power.get("actions"), "power.actions"),
      "action_names": _text_mapping(action_names, "power.action_names"),
      "usage_key": _text(power.get("usage_key"), "power.usage_key"),
      "failed_key": _text(power.get("failed_key"), "power.failed_key"),
      "timing": {
        "wait_environment": _text(timing.get("wait_environment"), "power.timing.wait_environment"),
        "wait_default": _number(timing.get("wait_default"), "power.timing.wait_default"),
        "controller_query_timeout": _number(timing.get("controller_query_timeout"), "power.timing.controller_query_timeout"),
        "show_timeout": _number(timing.get("show_timeout"), "power.timing.show_timeout"),
        "power_timeout": _number(timing.get("power_timeout"), "power.timing.power_timeout"),
        "poll_interval": _number(timing.get("poll_interval"), "power.timing.poll_interval"),
      },
      "fields": {
        "controller_address": _integer(fields.get("controller_address"), "power.fields.controller_address"),
        "powered_text": _text(fields.get("powered_text"), "power.fields.powered_text"),
      },
      "commands": {
        "controller_list": _text_list(power_commands.get("controller_list"), "power.commands.controller_list"),
        "controller_show": _text_list(power_commands.get("controller_show"), "power.commands.controller_show"),
        "power_on": _text_list(power_commands.get("power_on"), "power.commands.power_on"),
      },
    },
  }


def command(config: BluetoothConfig, name: RunCommandName, arguments: list[str] | None = None) -> list[str]:
  return [*config["commands"][name], *(arguments or [])]


def run(
  config: BluetoothConfig,
  name: RunCommandName,
  arguments: list[str] | None = None,
  timeout_seconds: float | None = None,
  capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
  argv = command(config, name, arguments)
  if timeout_seconds is not None:
    argv = [*config["commands"]["timeout"], f"{timeout_seconds}{config['commands']['timeout_unit']}", *argv]
  if capture_output:
    return subprocess.run(argv, check=False, capture_output=True, text=True)
  return subprocess.run(argv, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)


def translated(config: BluetoothConfig, key: str) -> str:
  try:
    result = subprocess.run(command(config, "i18n", [key]), check=False, capture_output=True, text=True)
  except OSError:
    return key
  return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else key


def _device_main(arguments: list[str], config: BluetoothConfig) -> int:
  device = config["device"]
  if len(arguments) != 2 or arguments[0] not in device["actions"] or not re.fullmatch(device["address_pattern"], arguments[1]):
    print(translated(config, device["usage_key"]), file=sys.stderr)
    return 2

  action, address = arguments
  query = device["powered_query"]
  state = run(config, query["command"], query["arguments"], query["timeout"], capture_output=True)
  if query["success_text"] not in state.stdout:
    ensure = device["ensure_power"]
    result = subprocess.run(command(config, ensure["command"], ensure["arguments"]), check=False)
    if result.returncode and not ensure["ignore_failure"]:
      return result.returncode

  for step in device["action_commands"][action]:
    subcommand = config["commands"]["device"][step["command"]]
    result = run(config, "bluetoothctl", [*subcommand, address], step.get("timeout"))
    if result.returncode and step["required"]:
      return result.returncode
  return 0


def controllers(config: BluetoothConfig) -> list[str]:
  timing = config["power"]["timing"]
  values = config["power"]["fields"]
  result = run(
    config,
    "bluetoothctl",
    config["power"]["commands"]["controller_list"],
    timing["controller_query_timeout"],
    capture_output=True,
  )
  addresses: list[str] = []
  for line in result.stdout.splitlines():
    fields = line.split()
    index = values["controller_address"]
    if len(fields) > index:
      addresses.append(fields[index])
  return addresses


def powered(config: BluetoothConfig) -> bool:
  power = config["power"]
  for address in controllers(config):
    result = run(
      config,
      "bluetoothctl",
      [*power["commands"]["controller_show"], address],
      power["timing"]["show_timeout"],
      capture_output=True,
    )
    if power["fields"]["powered_text"] in result.stdout:
      return True
  return False


def wait_powered(config: BluetoothConfig, seconds: float) -> bool:
  poll = config["power"]["timing"]["poll_interval"]
  deadline = time.monotonic() + seconds
  while True:
    if powered(config):
      return True
    if time.monotonic() >= deadline:
      return False
    run(config, "sleep", [str(poll)])


def power_on(config: BluetoothConfig) -> int:
  power = config["power"]
  rfkill = config["commands"]["rfkill"]
  subprocess.run([*rfkill, *config["commands"]["rfkill_actions"]["unblock"]], check=True)
  timing = power["timing"]
  configured_wait = os.environ.get(timing["wait_environment"])
  wait_seconds = (
    float(configured_wait)
    if configured_wait is not None and configured_wait != ""
    else float(timing["wait_default"])
  )
  if wait_powered(config, wait_seconds):
    return 0

  result = run(
    config,
    "bluetoothctl",
    power["commands"]["power_on"],
    timing["power_timeout"],
  )
  if wait_powered(config, wait_seconds):
    return 0
  print(translated(config, power["failed_key"]), file=sys.stderr)
  return result.returncode or 1


def _power_main(arguments: list[str], config: BluetoothConfig) -> int:
  power = config["power"]
  if len(arguments) != 1 or arguments[0] not in power["actions"]:
    print(translated(config, power["usage_key"]), file=sys.stderr)
    return 2

  action = arguments[0]
  action_names = power["action_names"]
  if action == action_names["on"]:
    return power_on(config)
  if action == action_names["off"]:
    return subprocess.run(
      [*config["commands"]["rfkill"], *config["commands"]["rfkill_actions"]["block"]],
      check=False,
    ).returncode
  is_powered = powered(config)
  if action == action_names["is_on"]:
    return 0 if is_powered else 1
  if is_powered:
    return subprocess.run(
      [*config["commands"]["rfkill"], *config["commands"]["rfkill_actions"]["block"]],
      check=False,
    ).returncode
  return power_on(config)


def _entry(
  operation: Callable[[list[str], BluetoothConfig], int],
  arguments: list[str],
  label: str,
) -> int:
  try:
    config = load_config()
  except (OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load Bluetooth command configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    return operation(arguments, config)
  except (KeyError, OSError, re.error, subprocess.SubprocessError, TypeError, ValueError) as error:
    print(f"Could not {label}: {error}", file=sys.stderr)
    return os.EX_SOFTWARE


def device_main(arguments: list[str]) -> int:
  return _entry(_device_main, arguments, "control Bluetooth device")


def power_main(arguments: list[str]) -> int:
  return _entry(_power_main, arguments, "control Bluetooth power")
