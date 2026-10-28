from __future__ import annotations

import glob
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import TypedDict

import yaml


class Commands(TypedDict):
  power_supply: list[str]
  i18n: list[str]


class Flags(TypedDict):
  power_supply_enumerate: str
  power_supply_info: str
  number: str
  shell: str


Paths = dict[str, str]
Patterns = dict[str, str]

class Formulas(TypedDict):
  minutes_per_hour: int
  minutes_rounding_offset: float
  micro_units_per_watt: int
  microamp_microvolt_units_per_watt: int
  idle_rate_threshold_watts: float
  percentage_scale: int
  holding_below_percent: int
  fully_charged_percent: int
  default_charge_limit_percent: int
  missing_percentage: int
  missing_rate_watts: int
  rate_decimal_places: int
  zero_rate_suffix: str


class ShellFields(TypedDict):
  percentage: str
  state: str
  rate: str
  size: str
  time: str
  cycles: str
  threshold: str


class Formats(TypedDict):
  percentage_sign: str
  watt_unit: str
  watt_hour_unit: str
  ac_type: str
  online_value: str
  holding_state: str
  shell_fields: ShellFields
  hour_unit_prefix: str
  separator: str
  no_break_space: str
  charge_arrow: str
  discharge_arrow: str
  power_separator: str
  threshold_range_separator: str


class States(TypedDict):
  charging: str
  fully_charged: str
  pending_charge: str


Messages = dict[str, str]


class Statuses(TypedDict):
  usage: int
  success: int


class BatteryConfig(TypedDict):
  commands: Commands
  flags: Flags
  environment: dict[str, str]
  paths: Paths
  patterns: Patterns
  formulas: Formulas
  format: Formats
  states: States
  messages: Messages
  statuses: Statuses


class BatteryValues(TypedDict):
  percentage: int
  capacity: int | str
  energy: float | None
  energy_full: float | None
  rate_raw: float
  rate: str
  state: str
  threshold_start: str
  threshold_end: str
  minutes_remaining: int | None
  time_remaining: str
  ac_online: bool
  charge_idle: bool
  holding: bool
  battery_full: bool
  cycles: str


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid battery status configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid battery status configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid battery status configuration: {label} must be an integer")
  return value


def _number(value: object, label: str) -> int | float:
  if not isinstance(value, (int, float)) or isinstance(value, bool):
    raise ValueError(f"invalid battery status configuration: {label} must be numeric")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid battery status configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _text_mapping(value: object, label: str) -> dict[str, str]:
  mapping = _mapping(value, label)
  return {
    _text(key, f"{label} key"): _text(item, f"{label} value")
    for key, item in mapping.items()
  }


def settings() -> BatteryConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/battery-status.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  commands = _mapping(config.get("commands"), "commands")
  flags = _mapping(config.get("flags"), "flags")
  environment = _mapping(config.get("environment"), "environment")
  paths = _mapping(config.get("paths"), "paths")
  patterns = _mapping(config.get("patterns"), "patterns")
  formulas = _mapping(config.get("formulas"), "formulas")
  formats = _mapping(config.get("format"), "format")
  shell_fields = _mapping(formats.get("shell_fields"), "format.shell_fields")
  states = _mapping(config.get("states"), "states")
  messages = _mapping(config.get("messages"), "messages")
  statuses = _mapping(config.get("statuses"), "statuses")
  return {
    "commands": {
      "power_supply": _text_list(commands.get("power_supply"), "commands.power_supply"),
      "i18n": _text_list(commands.get("i18n"), "commands.i18n"),
    },
    "flags": {
      "power_supply_enumerate": _text(flags.get("power_supply_enumerate"), "flags.power_supply_enumerate"),
      "power_supply_info": _text(flags.get("power_supply_info"), "flags.power_supply_info"),
      "number": _text(flags.get("number"), "flags.number"),
      "shell": _text(flags.get("shell"), "flags.shell"),
    },
    "environment": {"power_supply_path": _text(environment.get("power_supply_path"), "environment.power_supply_path")},
    "paths": _text_mapping(paths, "paths"),
    "patterns": _text_mapping(patterns, "patterns"),
    "formulas": {
      "minutes_per_hour": _integer(formulas.get("minutes_per_hour"), "formulas.minutes_per_hour"),
      "minutes_rounding_offset": _number(formulas.get("minutes_rounding_offset"), "formulas.minutes_rounding_offset"),
      "micro_units_per_watt": _integer(formulas.get("micro_units_per_watt"), "formulas.micro_units_per_watt"),
      "microamp_microvolt_units_per_watt": _integer(formulas.get("microamp_microvolt_units_per_watt"), "formulas.microamp_microvolt_units_per_watt"),
      "idle_rate_threshold_watts": _number(formulas.get("idle_rate_threshold_watts"), "formulas.idle_rate_threshold_watts"),
      "percentage_scale": _integer(formulas.get("percentage_scale"), "formulas.percentage_scale"),
      "holding_below_percent": _integer(formulas.get("holding_below_percent"), "formulas.holding_below_percent"),
      "fully_charged_percent": _integer(formulas.get("fully_charged_percent"), "formulas.fully_charged_percent"),
      "default_charge_limit_percent": _integer(formulas.get("default_charge_limit_percent"), "formulas.default_charge_limit_percent"),
      "missing_percentage": _integer(formulas.get("missing_percentage"), "formulas.missing_percentage"),
      "missing_rate_watts": _integer(formulas.get("missing_rate_watts"), "formulas.missing_rate_watts"),
      "rate_decimal_places": _integer(formulas.get("rate_decimal_places"), "formulas.rate_decimal_places"),
      "zero_rate_suffix": _text(formulas.get("zero_rate_suffix"), "formulas.zero_rate_suffix"),
    },
    "format": {
      "percentage_sign": _text(formats.get("percentage_sign"), "format.percentage_sign"),
      "watt_unit": _text(formats.get("watt_unit"), "format.watt_unit"),
      "watt_hour_unit": _text(formats.get("watt_hour_unit"), "format.watt_hour_unit"),
      "ac_type": _text(formats.get("ac_type"), "format.ac_type"),
      "online_value": _text(formats.get("online_value"), "format.online_value"),
      "holding_state": _text(formats.get("holding_state"), "format.holding_state"),
      "shell_fields": {
        "percentage": _text(shell_fields.get("percentage"), "format.shell_fields.percentage"),
        "state": _text(shell_fields.get("state"), "format.shell_fields.state"),
        "rate": _text(shell_fields.get("rate"), "format.shell_fields.rate"),
        "size": _text(shell_fields.get("size"), "format.shell_fields.size"),
        "time": _text(shell_fields.get("time"), "format.shell_fields.time"),
        "cycles": _text(shell_fields.get("cycles"), "format.shell_fields.cycles"),
        "threshold": _text(shell_fields.get("threshold"), "format.shell_fields.threshold"),
      },
      "hour_unit_prefix": _text(formats.get("hour_unit_prefix"), "format.hour_unit_prefix"),
      "separator": _text(formats.get("separator"), "format.separator"),
      "no_break_space": _text(formats.get("no_break_space"), "format.no_break_space"),
      "charge_arrow": _text(formats.get("charge_arrow"), "format.charge_arrow"),
      "discharge_arrow": _text(formats.get("discharge_arrow"), "format.discharge_arrow"),
      "power_separator": _text(formats.get("power_separator"), "format.power_separator"),
      "threshold_range_separator": _text(formats.get("threshold_range_separator"), "format.threshold_range_separator"),
    },
    "states": {
      "charging": _text(states.get("charging"), "states.charging"),
      "fully_charged": _text(states.get("fully_charged"), "states.fully_charged"),
      "pending_charge": _text(states.get("pending_charge"), "states.pending_charge"),
    },
    "messages": _text_mapping(messages, "messages"),
    "statuses": {
      "usage": _integer(statuses.get("usage"), "statuses.usage"),
      "success": _integer(statuses.get("success"), "statuses.success"),
    },
  }


def match(config: BatteryConfig, key: str, text: str) -> re.Match[str] | None:
  return re.search(config["patterns"][key], text, re.MULTILINE)


def capture(config: BatteryConfig, key: str, text: str, group: int = 1, default: str = "") -> str:
  result = match(config, key, text)
  if result is None:
    return default
  value = result.group(group)
  return value if isinstance(value, str) else default


def run(
  command: list[str],
  *,
  capture_output: bool = False,
  stdout: int | None = None,
  stderr: int | None = None,
) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    command,
    check=False,
    text=True,
    capture_output=capture_output,
    stdout=stdout,
    stderr=stderr,
  )


def localized(config: BatteryConfig, key: str, *arguments: str | int | float) -> str:
  result = run([*config["commands"]["i18n"], key, *(str(value) for value in arguments)], capture_output=True)
  return result.stdout.rstrip("\n")


def format_duration(config: BatteryConfig, minutes: int | None) -> str:
  if minutes is None or minutes <= 0:
    return ""
  per_hour = int(config["formulas"]["minutes_per_hour"])
  hours, remainder = divmod(minutes, per_hour)
  if minutes < per_hour:
    return localized(config, config["messages"]["duration_minutes"], minutes)
  if remainder == 0:
    return localized(config, config["messages"]["duration_hours"], hours)
  return localized(config, config["messages"]["duration_hours_minutes"], hours, remainder)


def first_file(directory: Path, basename: str) -> str:
  path = directory / basename
  try:
    return path.read_text(encoding="utf-8").strip()
  except OSError:
    return ""


def legacy_value(config: BatteryConfig, root: Path, filename: str) -> str:
  pattern = str(root / config["paths"]["legacy_battery_glob"] / filename)
  for path in sorted(Path(item) for item in glob.glob(pattern)):
    try:
      return path.read_text(encoding="utf-8").strip()
    except OSError:
      continue
  return ""


def number(config: BatteryConfig, value: str | int | float) -> str:
  return localized(config, config["flags"]["number"], value)


def battery_info(config: BatteryConfig) -> tuple[str, str]:
  result = run(config["commands"]["power_supply"] + [config["flags"]["power_supply_enumerate"]], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  for candidate in result.stdout.splitlines():
    if config["patterns"]["battery_identifier"] not in candidate:
      continue
    info = run(config["commands"]["power_supply"] + [config["flags"]["power_supply_info"], candidate], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if info.returncode != 0:
      continue
    if match(config, "power_supply", info.stdout):
      return candidate, info.stdout
  return "", ""


def read_values(config: BatteryConfig, info: str, root: Path) -> BatteryValues:
  paths = config["paths"]
  formulas = config["formulas"]
  states = config["states"]
  percentage_match = match(config, "percentage", info)
  capacity_match = match(config, "capacity", info)
  energy_match = match(config, "energy", info)
  energy_full_match = match(config, "energy_full", info)
  remaining_match = match(config, "time_remaining", info)
  native_path = capture(config, "native_path", info)
  native_path_value = Path(native_path)
  battery_path = root / native_path_value if native_path and not native_path_value.is_absolute() and ".." not in native_path_value.parts else root / paths["invalid_native_path"]

  percentage = int(float(percentage_match.group(1))) if percentage_match else int(formulas["missing_percentage"])
  capacity = int(float(capacity_match.group(1))) if capacity_match else ""
  energy = float(energy_match.group(1)) if energy_match else None
  energy_full = float(energy_full_match.group(1)) if energy_full_match else None
  upower_hours: float | None = None
  if remaining_match:
    upower_hours = float(remaining_match.group(1))
    if remaining_match.group(2).startswith(config["format"]["hour_unit_prefix"]):
      upower_hours /= float(formulas["minutes_per_hour"])

  power_rate_raw = capture(config, "energy_rate", info, default=str(formulas["missing_rate_watts"]))
  power_file = first_file(battery_path, paths["power_now"])
  if power_file:
    power_rate_raw = str(float(power_file) / float(formulas["micro_units_per_watt"]))
  else:
    current = first_file(battery_path, paths["current_now"])
    voltage = first_file(battery_path, paths["voltage_now"])
    if current and voltage:
      power_rate_raw = str(float(current) * float(voltage) / float(formulas["microamp_microvolt_units_per_watt"]))

  raw_rate = float(power_rate_raw or formulas["missing_rate_watts"])
  absolute_rate = abs(raw_rate)
  power_rate = f"{absolute_rate:.{int(formulas['rate_decimal_places'])}f}"
  zero_suffix = config["formulas"]["zero_rate_suffix"]
  if power_rate.endswith(zero_suffix):
    power_rate = power_rate[:-len(zero_suffix)]

  state = capture(config, "state", info)
  threshold_start = capture(config, "charge_start_threshold", info)
  threshold_end = capture(config, "charge_end_threshold", info)
  if not threshold_end:
    threshold_end = first_file(battery_path, paths["charge_control_end_threshold"])
  if not threshold_start:
    threshold_start = first_file(battery_path, paths["charge_control_start_threshold"])

  charge_limit = float(threshold_end or formulas["default_charge_limit_percent"])
  if not threshold_end:
    threshold_end = legacy_value(config, root, paths["charge_control_end_threshold"])
  if not threshold_start:
    threshold_start = legacy_value(config, root, paths["charge_control_start_threshold"])

  if energy is not None and energy_full is not None and absolute_rate > float(formulas["idle_rate_threshold_watts"]):
    hours = ((energy_full * charge_limit / float(formulas["percentage_scale"])) - energy) / absolute_rate if state == states["charging"] else energy / absolute_rate
  else:
    hours = upower_hours
  minutes_remaining: int | None = None
  if hours is not None and hours > 0:
    minutes_remaining = math.floor(hours * int(formulas["minutes_per_hour"]) + float(formulas["minutes_rounding_offset"]))

  try:
    supplies = list(root.iterdir())
  except OSError:
    supplies = []
  ac_online = any(
    first_file(supply, paths["type"]) == config["format"]["ac_type"]
    and first_file(supply, paths["online"]) == config["format"]["online_value"]
    for supply in supplies if supply.is_dir()
  )
  charge_idle = absolute_rate <= float(formulas["idle_rate_threshold_watts"])
  holding = False
  if ac_online and threshold_end:
    end_threshold = int(float(threshold_end))
    if state == states["pending_charge"]:
      holding = True
    elif state == states["fully_charged"] and percentage < int(formulas["holding_below_percent"]):
      holding = True
    elif state == states["charging"] and charge_idle and end_threshold < int(formulas["holding_below_percent"]) and percentage >= end_threshold:
      holding = True

  cycles = first_file(battery_path, paths["cycle_count"]) or legacy_value(config, root, paths["cycle_count"])
  return {
    "percentage": percentage,
    "capacity": capacity,
    "energy": energy,
    "energy_full": energy_full,
    "rate_raw": raw_rate,
    "rate": power_rate,
    "state": state,
    "threshold_start": threshold_start,
    "threshold_end": threshold_end,
    "minutes_remaining": minutes_remaining,
    "time_remaining": format_duration(config, minutes_remaining),
    "ac_online": ac_online,
    "charge_idle": charge_idle,
    "holding": holding,
    "battery_full": state == states["fully_charged"] or (ac_online and percentage >= int(formulas["fully_charged_percent"])),
    "cycles": cycles,
  }


def shell_output(config: BatteryConfig, values: BatteryValues) -> None:
  fields = config["format"]["shell_fields"]
  percentage = f"{values['percentage']}{config['format']['percentage_sign']}"
  state = config["format"]["holding_state"] if values["holding"] else values["state"]
  output = [
    (fields["percentage"], percentage),
    (fields["state"], state),
    (fields["rate"], f"{values['rate']}{config['format']['watt_unit']}"),
    (fields["size"], f"{values['capacity']}{config['format']['watt_hour_unit']}"),
    (fields["time"], values["time_remaining"]),
  ]
  for key, value in output:
    print(f"{key}\t{value}")
  if values["cycles"]:
    print(f"{fields['cycles']}\t{values['cycles']}")
  if values["threshold_end"]:
    if values["threshold_start"] and values["threshold_start"] != values["threshold_end"]:
      threshold = f"{values['threshold_start']}{config['format']['threshold_range_separator']}{values['threshold_end']}{config['format']['percentage_sign']}"
    else:
      threshold = f"{values['threshold_end']}{config['format']['percentage_sign']}"
    print(f"{fields['threshold']}\t{threshold}")


def status_line(config: BatteryConfig, values: BatteryValues) -> str:
  messages = config["messages"]
  formats = config["format"]
  states = config["states"]
  percentage = values["percentage"]
  parts = [localized(config, messages["status_label"], percentage)]
  if values["holding"]:
    start, end = values["threshold_start"], values["threshold_end"]
    threshold = f"{number(config, start)}{formats['threshold_range_separator']}{number(config, end)}{formats['percentage_sign']}" if start and start != end else f"{number(config, end)}{formats['percentage_sign']}"
    parts.append(localized(config, messages["holding_at"], threshold))
  elif values["battery_full"]:
    parts.append(localized(config, messages["fully_charged"]))
  elif values["time_remaining"] and values["state"] == states["charging"]:
    parts.append(localized(config, messages["to_full"], values["time_remaining"]))
  elif values["time_remaining"]:
    parts.append(localized(config, messages["time_left"], values["time_remaining"]))

  capacity = values["capacity"]
  capacity_reading = f"{number(config, capacity)}{formats['watt_hour_unit']}" if capacity and int(capacity) > 0 else ""
  if not values["holding"] and not values["battery_full"] and not values["charge_idle"]:
    arrow_key = "charge_arrow" if values["state"] == states["charging"] else "discharge_arrow"
    draw = f"{formats[arrow_key]}{formats['no_break_space']}{number(config, values['rate'])}{formats['watt_unit']}"
    if capacity_reading:
      draw = f"{draw}{formats['no_break_space']}{formats['power_separator']}{formats['no_break_space']}{capacity_reading}"
    parts.append(draw)
  elif capacity_reading:
    parts.append(capacity_reading)
  return formats["separator"].join(parts)


def _run(config: BatteryConfig, arguments: list[str]) -> int:
  shell_flag = config["flags"]["shell"]
  shell_mode = arguments == [shell_flag]
  if arguments not in ([], [shell_flag]):
    print(localized(config, config["messages"]["usage"]), file=sys.stderr)
    return config["statuses"]["usage"]

  root = Path(os.environ.get(config["environment"]["power_supply_path"], config["paths"]["default_power_supply_path"]))
  _, info = battery_info(config)
  if not info:
    return config["statuses"]["success"]
  values = read_values(config, info, root)
  if shell_mode:
    shell_output(config, values)
  else:
    print(status_line(config, values))
  return config["statuses"]["success"]


def main() -> int:
  try:
    config = settings()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load battery status configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  try:
    return _run(config, sys.argv[1:])
  except (KeyError, OSError, re.error, subprocess.SubprocessError, TypeError, ValueError) as error:
    print(f"Could not read battery status: {error}", file=sys.stderr)
    return os.EX_SOFTWARE


if __name__ == "__main__":
  raise SystemExit(main())
