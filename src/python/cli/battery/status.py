from __future__ import annotations

import glob
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml


def settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  value = yaml.safe_load((root / "data/cli/battery-status.yml").read_text(encoding="utf-8"))
  if not isinstance(value, dict):
    raise ValueError("invalid battery status configuration")
  return value


def match(config: dict[str, Any], key: str, text: str) -> re.Match[str] | None:
  return re.search(config["patterns"][key], text, re.MULTILINE)


def capture(config: dict[str, Any], key: str, text: str, group: int = 1, default: str = "") -> str:
  result = match(config, key, text)
  return result.group(group) if result else default


def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
  return subprocess.run(command, check=False, text=True, **kwargs)


def localized(config: dict[str, Any], key: str, *arguments: object) -> str:
  result = run([*config["commands"]["i18n"], key, *(str(value) for value in arguments)], capture_output=True)
  return result.stdout.rstrip("\n")


def format_duration(config: dict[str, Any], minutes: int | None) -> str:
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


def legacy_value(config: dict[str, Any], root: Path, filename: str) -> str:
  pattern = str(root / config["paths"]["legacy_battery_glob"] / filename)
  for path in sorted(Path(item) for item in glob.glob(pattern)):
    try:
      return path.read_text(encoding="utf-8").strip()
    except OSError:
      continue
  return ""


def number(config: dict[str, Any], value: object) -> str:
  return localized(config, config["flags"]["number"], value)


def battery_info(config: dict[str, Any]) -> tuple[str, str]:
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


def read_values(config: dict[str, Any], info: str, root: Path) -> dict[str, Any]:
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


def shell_output(config: dict[str, Any], values: dict[str, Any]) -> None:
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


def status_line(config: dict[str, Any], values: dict[str, Any]) -> str:
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


def main() -> int:
  config = settings()
  arguments = sys.argv[1:]
  shell_flag = config["flags"]["shell"]
  shell_mode = arguments == [shell_flag]
  if arguments not in ([], [shell_flag]):
    print(localized(config, config["messages"]["usage"]), file=sys.stderr)
    return int(config["statuses"]["usage"])

  root = Path(os.environ.get(config["environment"]["power_supply_path"], config["paths"]["default_power_supply_path"]))
  _, info = battery_info(config)
  if not info:
    return int(config["statuses"]["success"])
  values = read_values(config, info, root)
  if shell_mode:
    shell_output(config, values)
  else:
    print(status_line(config, values))
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
