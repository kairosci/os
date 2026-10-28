"""Build a shareable QR matrix for the current Wi-Fi connection."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/network-qr.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid Wi-Fi QR configuration")
  return config


def run(
  arguments: list[str],
  *,
  capture: bool = True,
  input_text: str | None = None,
  environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str] | None:
  try:
    return subprocess.run(
      arguments,
      check=False,
      capture_output=capture,
      text=True,
      input=input_text,
      env=environment,
    )
  except OSError:
    return None


def localized(config: dict[str, Any], key: str) -> str:
  result = run([*config["commands"]["i18n"], config["messages"][key]])
  if result is None or result.returncode != int(config["statuses"]["success"]):
    return ""
  return result.stdout.rstrip("\n")


def fail(config: dict[str, Any], key: str) -> int:
  print(localized(config, key), file=sys.stderr)
  return int(config["statuses"]["failure"])


def valid_interface(interface: str, config: dict[str, Any]) -> bool:
  return re.fullmatch(config["interface"]["pattern"], interface) is not None


def connected_fallback(config: dict[str, Any]) -> str:
  env = {**os.environ, **config["environment"]["stable_locale"]}
  result = run(config["commands"]["nmcli_device_status"], environment=env)
  if result is None or result.returncode != int(config["statuses"]["success"]):
    return ""
  for line in result.stdout.splitlines():
    fields = line.split(config["formats"]["nmcli_separator"], int(config["formats"]["nmcli_field_limit"]))
    if len(fields) != int(config["formats"]["nmcli_field_count"]):
      continue
    device, device_type, state = fields
    if device_type == config["network"]["wireless_type"] and state.startswith(config["network"]["connected_prefix"]):
      if valid_interface(device, config):
        return device
  return ""


def default_interface(config: dict[str, Any]) -> str:
  route = run([*config["commands"]["ip_route_get"], config["network"]["route_target"]])
  if route is not None and route.returncode == int(config["statuses"]["success"]):
    match = re.search(config["patterns"]["route_device"], route.stdout)
    if match is not None:
      device = match.group(config["patterns"]["route_device_group"])
      wireless_path = config["paths"]["wireless_class_template"].format(interface=device)
      if valid_interface(device, config) and Path(wireless_path).is_dir():
        return device
  return connected_fallback(config)


def connection_uuid(interface: str, config: dict[str, Any]) -> str:
  result = run([*config["commands"]["nmcli_uuid"], interface])
  if result is None or result.returncode != int(config["statuses"]["success"]):
    return ""
  value = next(iter(result.stdout.splitlines()), "")
  if value == config["network"]["empty_nmcli_value"]:
    return ""
  return value


def connection_fields(uuid: str, config: dict[str, Any]) -> list[str] | None:
  result = run([*config["commands"]["nmcli_connection_fields"], uuid])
  if result is None or result.returncode != int(config["statuses"]["success"]):
    return None
  fields = result.stdout.splitlines()
  required = int(config["formats"]["connection_field_count"])
  if len(fields) < required:
    fields.extend([""] * (required - len(fields)))
  return fields[:required]


def escape_wifi_field(value: str, config: dict[str, Any]) -> str:
  for item in config["encoding"]["escapes"]:
    value = value.replace(item["character"], item["replacement"])
  return value


def payload_error(fields: list[str], config: dict[str, Any]) -> str | None:
  ssid, key_management, password, _, _ = fields
  if not ssid:
    return "ssid_unavailable"
  management = key_management.casefold()
  if any(marker in management for marker in config["network"]["enterprise_markers"]):
    return "enterprise_network"
  if key_management and key_management != config["network"]["no_key_management"] and not password:
    return "password_unavailable"
  return None


def wifi_payload(fields: list[str], config: dict[str, Any]) -> tuple[str, str] | None:
  if payload_error(fields, config) is not None:
    return None
  ssid, key_management, password, hidden, wep_key = fields
  security_values = config["network"]["security"]
  security = security_values["open"]
  if key_management and key_management != config["network"]["no_key_management"]:
    security = security_values["wpa"]
  elif wep_key:
    password = wep_key
    security = security_values["wep"]
  payload = config["encoding"]["payload_template"].format(
    security=security,
    ssid=escape_wifi_field(ssid, config),
    password=escape_wifi_field(password, config),
  )
  if hidden == config["network"]["hidden_value"]:
    payload += config["encoding"]["hidden_suffix"]
  return payload + config["encoding"]["terminator"], security


def qr_matrix(payload: str, config: dict[str, Any]) -> list[str] | None:
  result = run([*config["commands"]["qrencode"]], input_text=payload)
  if result is None or result.returncode != int(config["statuses"]["success"]):
    return None
  matrix: list[str] = []
  pair_width = int(config["encoding"]["ascii_pair_width"])
  filled = config["encoding"]["ascii_filled"]
  for line in result.stdout.splitlines():
    row = "".join(
      config["encoding"]["matrix_on"] if filled in line[offset:offset + pair_width]
      else config["encoding"]["matrix_off"]
      for offset in range(0, len(line), pair_width)
    )
    matrix.append(row)
  return matrix


def parse_arguments(arguments: list[str], config: dict[str, Any]) -> tuple[bool, str] | None:
  meta_flag = config["arguments"]["meta_flag"]
  interfaces = [argument for argument in arguments if argument != meta_flag]
  if len(interfaces) > int(config["formats"]["maximum_interfaces"]):
    return None
  interface = interfaces[0] if interfaces else ""
  if interface and not valid_interface(interface, config):
    return None
  return meta_flag in arguments, interface


def main(arguments: list[str] | None = None) -> int:
  config: dict[str, Any] = {}
  try:
    config = load_config()
    supplied = sys.argv[1:] if arguments is None else arguments
    parsed = parse_arguments(supplied, config)
    if parsed is None:
      return fail(config, "usage")
    emit_meta, interface = parsed
    interface = interface or default_interface(config)
    if not interface:
      return fail(config, "no_connection")
    uuid = connection_uuid(interface, config)
    if not uuid:
      return fail(config, "no_connection")
    fields = connection_fields(uuid, config)
    if fields is None:
      return fail(config, "connection_unavailable")
    error_key = payload_error(fields, config)
    if error_key is not None:
      return fail(config, error_key)
    encoded = wifi_payload(fields, config)
    if encoded is None:
      return fail(config, "connection_unavailable")
    payload, security = encoded
    matrix = qr_matrix(payload, config)
    if matrix is None:
      return fail(config, "generation_failed")
    if emit_meta:
      ssid = fields[0]
      print(config["formats"]["metadata_template"].format(interface=interface, security=security, ssid=ssid))
    for row in matrix:
      print(row)
    return int(config["statuses"]["success"])
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    if config:
      try:
        return fail(config, "configuration_invalid")
      except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
        pass
    return int(config.get("statuses", {}).get("configuration_failure", os.EX_CONFIG))


if __name__ == "__main__":
  raise SystemExit(main())
