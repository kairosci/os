"""Build a shareable QR matrix for the current Wi-Fi connection."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from typing import TypedDict

import yaml


class Commands(TypedDict):
  i18n: list[str]
  ip_route_get: list[str]
  nmcli_device_status: list[str]
  nmcli_uuid: list[str]
  nmcli_connection_fields: list[str]
  qrencode: list[str]


class Interface(TypedDict):
  pattern: str


class Security(TypedDict):
  wpa: str
  wep: str
  open: str


class Network(TypedDict):
  route_target: str
  wireless_type: str
  connected_prefix: str
  empty_nmcli_value: str
  no_key_management: str
  hidden_value: str
  enterprise_markers: list[str]
  security: Security


class Paths(TypedDict):
  wireless_class_template: str


class Patterns(TypedDict):
  route_device: str
  route_device_group: int


class Arguments(TypedDict):
  meta_flag: str


class Formats(TypedDict):
  nmcli_separator: str
  nmcli_field_limit: int
  nmcli_field_count: int
  connection_field_count: int
  maximum_interfaces: int
  metadata_template: str


class Escape(TypedDict):
  character: str
  replacement: str


class Encoding(TypedDict):
  payload_template: str
  hidden_suffix: str
  terminator: str
  escapes: list[Escape]
  ascii_pair_width: int
  ascii_filled: str
  matrix_on: str
  matrix_off: str


class Statuses(TypedDict):
  success: int
  failure: int
  configuration_failure: int


class WifiQrConfig(TypedDict):
  commands: Commands
  environment: dict[str, dict[str, str]]
  interface: Interface
  network: Network
  paths: Paths
  patterns: Patterns
  arguments: Arguments
  formats: Formats
  encoding: Encoding
  messages: dict[str, str]
  statuses: Statuses


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise ValueError(f"invalid Wi-Fi QR configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise ValueError(f"invalid Wi-Fi QR configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise ValueError(f"invalid Wi-Fi QR configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
    raise ValueError(f"invalid Wi-Fi QR configuration: {label} must be a list of strings")
  return [item for item in value if isinstance(item, str)]


def _text_mapping(value: object, label: str) -> dict[str, str]:
  mapping = _mapping(value, label)
  return {
    _text(key, f"{label} key"): _text(item, f"{label} value")
    for key, item in mapping.items()
  }


def _escapes(value: object) -> list[Escape]:
  if not isinstance(value, list):
    raise ValueError("invalid Wi-Fi QR configuration: encoding.escapes must be a list")
  escapes: list[Escape] = []
  for index, item in enumerate(value):
    escape = _mapping(item, f"encoding.escapes[{index}]")
    escapes.append({
      "character": _text(escape.get("character"), f"encoding.escapes[{index}].character"),
      "replacement": _text(escape.get("replacement"), f"encoding.escapes[{index}].replacement"),
    })
  return escapes


def _locale_environment(value: object) -> dict[str, dict[str, str]]:
  mapping = _mapping(value, "environment")
  stable_locale = _text_mapping(mapping.get("stable_locale"), "environment.stable_locale")
  return {"stable_locale": stable_locale}


def load_config() -> WifiQrConfig:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/network-qr.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  commands = _mapping(config.get("commands"), "commands")
  interface = _mapping(config.get("interface"), "interface")
  network = _mapping(config.get("network"), "network")
  security = _mapping(network.get("security"), "network.security")
  paths = _mapping(config.get("paths"), "paths")
  patterns = _mapping(config.get("patterns"), "patterns")
  arguments = _mapping(config.get("arguments"), "arguments")
  formats = _mapping(config.get("formats"), "formats")
  encoding = _mapping(config.get("encoding"), "encoding")
  statuses = _mapping(config.get("statuses"), "statuses")
  return {
    "commands": {
      "i18n": _text_list(commands.get("i18n"), "commands.i18n"),
      "ip_route_get": _text_list(commands.get("ip_route_get"), "commands.ip_route_get"),
      "nmcli_device_status": _text_list(commands.get("nmcli_device_status"), "commands.nmcli_device_status"),
      "nmcli_uuid": _text_list(commands.get("nmcli_uuid"), "commands.nmcli_uuid"),
      "nmcli_connection_fields": _text_list(
        commands.get("nmcli_connection_fields"), "commands.nmcli_connection_fields"
      ),
      "qrencode": _text_list(commands.get("qrencode"), "commands.qrencode"),
    },
    "environment": _locale_environment(config.get("environment")),
    "interface": {"pattern": _text(interface.get("pattern"), "interface.pattern")},
    "network": {
      "route_target": _text(network.get("route_target"), "network.route_target"),
      "wireless_type": _text(network.get("wireless_type"), "network.wireless_type"),
      "connected_prefix": _text(network.get("connected_prefix"), "network.connected_prefix"),
      "empty_nmcli_value": _text(network.get("empty_nmcli_value"), "network.empty_nmcli_value"),
      "no_key_management": _text(network.get("no_key_management"), "network.no_key_management"),
      "hidden_value": _text(network.get("hidden_value"), "network.hidden_value"),
      "enterprise_markers": _text_list(network.get("enterprise_markers"), "network.enterprise_markers"),
      "security": {
        "wpa": _text(security.get("wpa"), "network.security.wpa"),
        "wep": _text(security.get("wep"), "network.security.wep"),
        "open": _text(security.get("open"), "network.security.open"),
      },
    },
    "paths": {
      "wireless_class_template": _text(paths.get("wireless_class_template"), "paths.wireless_class_template")
    },
    "patterns": {
      "route_device": _text(patterns.get("route_device"), "patterns.route_device"),
      "route_device_group": _integer(patterns.get("route_device_group"), "patterns.route_device_group"),
    },
    "arguments": {"meta_flag": _text(arguments.get("meta_flag"), "arguments.meta_flag")},
    "formats": {
      "nmcli_separator": _text(formats.get("nmcli_separator"), "formats.nmcli_separator"),
      "nmcli_field_limit": _integer(formats.get("nmcli_field_limit"), "formats.nmcli_field_limit"),
      "nmcli_field_count": _integer(formats.get("nmcli_field_count"), "formats.nmcli_field_count"),
      "connection_field_count": _integer(
        formats.get("connection_field_count"), "formats.connection_field_count"
      ),
      "maximum_interfaces": _integer(formats.get("maximum_interfaces"), "formats.maximum_interfaces"),
      "metadata_template": _text(formats.get("metadata_template"), "formats.metadata_template"),
    },
    "encoding": {
      "payload_template": _text(encoding.get("payload_template"), "encoding.payload_template"),
      "hidden_suffix": _text(encoding.get("hidden_suffix"), "encoding.hidden_suffix"),
      "terminator": _text(encoding.get("terminator"), "encoding.terminator"),
      "escapes": _escapes(encoding.get("escapes")),
      "ascii_pair_width": _integer(encoding.get("ascii_pair_width"), "encoding.ascii_pair_width"),
      "ascii_filled": _text(encoding.get("ascii_filled"), "encoding.ascii_filled"),
      "matrix_on": _text(encoding.get("matrix_on"), "encoding.matrix_on"),
      "matrix_off": _text(encoding.get("matrix_off"), "encoding.matrix_off"),
    },
    "messages": _text_mapping(config.get("messages"), "messages"),
    "statuses": {
      "success": _integer(statuses.get("success"), "statuses.success"),
      "failure": _integer(statuses.get("failure"), "statuses.failure"),
      "configuration_failure": _integer(statuses.get("configuration_failure"), "statuses.configuration_failure"),
    },
  }


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


def localized(config: WifiQrConfig, key: str) -> str:
  result = run([*config["commands"]["i18n"], config["messages"][key]])
  if result is None or result.returncode != config["statuses"]["success"]:
    return ""
  return result.stdout.rstrip("\n")


def fail(config: WifiQrConfig, key: str) -> int:
  print(localized(config, key), file=sys.stderr)
  return config["statuses"]["failure"]


def valid_interface(interface: str, config: WifiQrConfig) -> bool:
  try:
    return re.fullmatch(config["interface"]["pattern"], interface) is not None
  except re.error:
    return False


def connected_fallback(config: WifiQrConfig) -> str:
  env = {**os.environ, **config["environment"]["stable_locale"]}
  result = run(config["commands"]["nmcli_device_status"], environment=env)
  if result is None or result.returncode != config["statuses"]["success"]:
    return ""
  for line in result.stdout.splitlines():
    fields = line.split(config["formats"]["nmcli_separator"], config["formats"]["nmcli_field_limit"])
    if len(fields) != config["formats"]["nmcli_field_count"]:
      continue
    device, device_type, state = fields
    if device_type == config["network"]["wireless_type"] and state.startswith(config["network"]["connected_prefix"]):
      if valid_interface(device, config):
        return device
  return ""


def default_interface(config: WifiQrConfig) -> str:
  route = run([*config["commands"]["ip_route_get"], config["network"]["route_target"]])
  if route is not None and route.returncode == config["statuses"]["success"]:
    match = re.search(config["patterns"]["route_device"], route.stdout)
    if match is not None:
      group = config["patterns"]["route_device_group"]
      if group > match.re.groups:
        return connected_fallback(config)
      matched_device = match.group(group)
      if not isinstance(matched_device, str):
        return connected_fallback(config)
      device = matched_device
      wireless_path = config["paths"]["wireless_class_template"].format(interface=device)
      if valid_interface(device, config) and Path(wireless_path).is_dir():
        return device
  return connected_fallback(config)


def connection_uuid(interface: str, config: WifiQrConfig) -> str:
  result = run([*config["commands"]["nmcli_uuid"], interface])
  if result is None or result.returncode != config["statuses"]["success"]:
    return ""
  value = next(iter(result.stdout.splitlines()), "")
  if value == config["network"]["empty_nmcli_value"]:
    return ""
  return value


def connection_fields(uuid: str, config: WifiQrConfig) -> list[str] | None:
  result = run([*config["commands"]["nmcli_connection_fields"], uuid])
  if result is None or result.returncode != config["statuses"]["success"]:
    return None
  fields = result.stdout.splitlines()
  required = config["formats"]["connection_field_count"]
  if len(fields) < required:
    fields.extend([""] * (required - len(fields)))
  return fields[:required]


def escape_wifi_field(value: str, config: WifiQrConfig) -> str:
  for item in config["encoding"]["escapes"]:
    value = value.replace(item["character"], item["replacement"])
  return value


def payload_error(fields: list[str], config: WifiQrConfig) -> str | None:
  ssid, key_management, password, _, _ = fields
  if not ssid:
    return "ssid_unavailable"
  management = key_management.casefold()
  if any(marker in management for marker in config["network"]["enterprise_markers"]):
    return "enterprise_network"
  if key_management and key_management != config["network"]["no_key_management"] and not password:
    return "password_unavailable"
  return None


def wifi_payload(fields: list[str], config: WifiQrConfig) -> tuple[str, str] | None:
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


def qr_matrix(payload: str, config: WifiQrConfig) -> list[str] | None:
  result = run([*config["commands"]["qrencode"]], input_text=payload)
  if result is None or result.returncode != config["statuses"]["success"]:
    return None
  matrix: list[str] = []
  pair_width = config["encoding"]["ascii_pair_width"]
  filled = config["encoding"]["ascii_filled"]
  for line in result.stdout.splitlines():
    row = "".join(
      config["encoding"]["matrix_on"] if filled in line[offset:offset + pair_width]
      else config["encoding"]["matrix_off"]
      for offset in range(0, len(line), pair_width)
    )
    matrix.append(row)
  return matrix


def parse_arguments(arguments: list[str], config: WifiQrConfig) -> tuple[bool, str] | None:
  meta_flag = config["arguments"]["meta_flag"]
  interfaces = [argument for argument in arguments if argument != meta_flag]
  if len(interfaces) > config["formats"]["maximum_interfaces"]:
    return None
  interface = interfaces[0] if interfaces else ""
  if interface and not valid_interface(interface, config):
    return None
  return meta_flag in arguments, interface


def main(arguments: list[str] | None = None) -> int:
  try:
    config = load_config()
  except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load Wi-Fi QR configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG

  try:
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
    return config["statuses"]["success"]
  except (KeyError, OSError, re.error, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not generate Wi-Fi QR code: {error}", file=sys.stderr)
    return config["statuses"]["configuration_failure"]


if __name__ == "__main__":
  raise SystemExit(main())
