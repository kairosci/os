from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/bluetooth.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("Invalid Bluetooth command configuration")
  return config


def command(config: dict[str, Any], name: str, arguments: list[str] | None = None) -> list[str]:
  return [*config["commands"][name], *(arguments or [])]


def run(
  config: dict[str, Any],
  name: str,
  arguments: list[str] | None = None,
  timeout_seconds: int | float | None = None,
  capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
  argv = command(config, name, arguments)
  if timeout_seconds is not None:
    argv = [*config["commands"]["timeout"], f"{timeout_seconds}{config['commands']['timeout_unit']}", *argv]
  if capture_output:
    return subprocess.run(argv, check=False, capture_output=True, text=True)
  return subprocess.run(argv, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def translated(config: dict[str, Any], key: str) -> str:
  result = subprocess.run(command(config, "i18n", [key]), check=False, capture_output=True, text=True)
  return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else key


def device_main(arguments: list[str]) -> int:
  config = load_config()
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


def controllers(config: dict[str, Any]) -> list[str]:
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


def powered(config: dict[str, Any]) -> bool:
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


def wait_powered(config: dict[str, Any], seconds: float) -> bool:
  poll = config["power"]["timing"]["poll_interval"]
  deadline = time.monotonic() + seconds
  while True:
    if powered(config):
      return True
    if time.monotonic() >= deadline:
      return False
    run(config, "sleep", [str(poll)])


def power_on(config: dict[str, Any]) -> int:
  power = config["power"]
  rfkill = config["commands"]["rfkill"]
  subprocess.run([*rfkill, *config["commands"]["rfkill_actions"]["unblock"]], check=True)
  timing = power["timing"]
  configured_wait = os.environ.get(timing["wait_environment"])
  wait_seconds = float(configured_wait) if configured_wait else float(timing["wait_default"])
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


def power_main(arguments: list[str]) -> int:
  config = load_config()
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
