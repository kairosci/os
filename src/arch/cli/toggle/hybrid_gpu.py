from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import cast

import yaml


def _settings() -> dict[str, object]:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/hybrid-gpu-toggle.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise ValueError("invalid hybrid GPU toggle configuration")
  document = cast(dict[object, object], raw)
  commands_raw = document.get("commands")
  settings_raw = document.get("settings")
  messages_raw = document.get("messages")
  if not all(isinstance(value, dict) for value in (commands_raw, settings_raw, messages_raw)):
    raise ValueError("invalid hybrid GPU toggle configuration")
  commands = cast(dict[object, object], commands_raw)
  settings = cast(dict[object, object], settings_raw)
  messages = cast(dict[object, object], messages_raw)
  if not all(
    isinstance(value, list) and value and all(isinstance(part, str) and part for part in value)
    for value in commands.values()
  ):
    raise ValueError("invalid hybrid GPU toggle commands")
  if not all(isinstance(value, str) and value for value in messages.values()):
    raise ValueError("invalid hybrid GPU toggle messages")
  config = settings.get("service_config_data")
  keys = settings.get("confirmation_keys")
  if not isinstance(config, dict) or not isinstance(keys, dict):
    raise ValueError("invalid hybrid GPU toggle settings")
  for name in ("query_timeout_seconds", "query_attempts", "retry_delay_seconds"):
    if type(settings.get(name)) is not int or cast(int, settings[name]) < 1:
      raise ValueError("invalid hybrid GPU query limits")
  for name in (
    "temporary_suffix_pattern", "temporary_file_template", "service_config", "service_config_mode", "integrated_mode", "hybrid_mode",
    "mode_key", "vfio_enable_key",
    "startup_delay_source", "startup_delay_destination", "startup_delay_mode", "sleep_hook_source",
    "sleep_hook_destination", "sleep_hook_mode", "drop_in_directory", "sleep_hook_directory",
  ):
    if not isinstance(settings.get(name), str) or not settings[name]:
      raise ValueError("incomplete hybrid GPU toggle settings")
  if not all(isinstance(value, str) and value for value in keys.values()):
    raise ValueError("invalid hybrid GPU confirmation keys")
  if type(settings.get("json_indent")) is not int or cast(int, settings["json_indent"]) < 0:
    raise ValueError("invalid hybrid GPU JSON indentation")
  return {"root": root, "commands": commands, "settings": settings, "messages": messages}


def _command(settings: dict[str, object], key: str) -> list[str]:
  commands = cast(dict[object, object], settings["commands"])
  return cast(list[str], commands[key])


def _run(
  arguments: list[str],
  *,
  capture: bool = False,
  timeout: int | None = None,
  input_data: str | None = None,
  discard_output: bool = False,
) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    arguments,
    check=False,
    stdout=subprocess.PIPE if capture else subprocess.DEVNULL if discard_output else None,
    stderr=subprocess.PIPE if capture else None,
    input=input_data,
    text=True,
    timeout=timeout,
  )


def _stage_path(settings: dict[str, object], destination: str) -> str | None:
  values = cast(dict[object, object], settings["settings"])
  template = cast(str, values["temporary_file_template"])
  directory = str(Path(destination).parent)
  name = Path(destination).name
  prefix = template.format(directory=directory, name=name).removesuffix("XXXXXX")
  name_template = template.format(directory=directory, name=name)
  result = _run(
    [*_command(settings, "sudo"), *_command(settings, "temp_file"), name_template],
    capture=True,
  )
  if result.returncode != 0:
    return None
  if result.stdout is None:
    return None
  stage = result.stdout.rstrip("\n")
  suffix_pattern = cast(str, cast(dict[object, object], settings["settings"])["temporary_suffix_pattern"])
  if not stage.startswith(prefix) or not re.fullmatch(suffix_pattern, stage.removeprefix(prefix)):
    return None
  return stage


def _install_root_file(settings: dict[str, object], source: Path, destination: str, mode: str) -> bool:
  stage = _stage_path(settings, destination)
  if stage is None:
    return False
  install = [
    *_command(settings, "sudo"),
    *_command(settings, "install"),
    mode,
    *_command(settings, "install_root_owned"),
    str(source),
    stage,
  ]
  publish = [*_command(settings, "sudo"), *_command(settings, "publish"), stage, destination]
  if _run(install).returncode == 0 and _run(publish).returncode == 0:
    return True
  _run([*_command(settings, "sudo"), *_command(settings, "remove"), stage])
  return False


def _install_root_content(settings: dict[str, object], content: str, destination: str, mode: str) -> bool:
  stage = _stage_path(settings, destination)
  if stage is None:
    return False
  operations = (
    ([*_command(settings, "sudo"), *_command(settings, "write_stage"), stage], content),
    ([*_command(settings, "sudo"), *_command(settings, "set_stage_mode"), mode, stage], None),
    ([*_command(settings, "sudo"), *_command(settings, "publish"), stage, destination], None),
  )
  for operation, input_data in operations:
    result = _run(operation, input_data=input_data, discard_output=input_data is not None)
    if result.returncode != 0:
      _run([*_command(settings, "sudo"), *_command(settings, "remove"), stage])
      return False
  return True


def _translate(settings: dict[str, object], key: str) -> str:
  keys = cast(dict[object, object], cast(dict[object, object], settings["settings"])["confirmation_keys"])
  result = _run([*_command(settings, "translate"), cast(str, keys[key])], capture=True)
  return result.stdout.rstrip("\n") if result.stdout is not None else ""


def _confirm(settings: dict[str, object], key: str) -> bool:
  result = _run(
    [*_command(settings, "confirm"), _translate(settings, "yes"), "--negative", _translate(settings, "no"), _translate(settings, key)]
  )
  return result.returncode == 0


def _query_mode(settings: dict[str, object]) -> str | None:
  values = cast(dict[object, object], settings["settings"])
  attempts = cast(int, values["query_attempts"])
  timeout = cast(int, values["query_timeout_seconds"])
  delay = cast(int, values["retry_delay_seconds"])
  for attempt in range(attempts):
    try:
      result = _run(
        [*_command(settings, "timeout"), f"{timeout}s", *_command(settings, "query_mode")],
        capture=True,
        timeout=timeout + 2,
      )
    except subprocess.TimeoutExpired:
      result = None
    if result is not None and result.returncode == 0 and result.stdout.strip():
      return result.stdout.strip()
    if attempt + 1 < attempts:
      _run([*_command(settings, "delay"), str(delay)])
  return None


def _write_service_config(settings: dict[str, object]) -> bool:
  values = cast(dict[object, object], settings["settings"])
  data = cast(dict[object, object], values["service_config_data"])
  serialized = json.dumps(data, indent=cast(int, values["json_indent"])) + "\n"
  return _install_root_content(
    settings,
    serialized,
    cast(str, values["service_config"]),
    cast(str, values["service_config_mode"]),
  )


def _switch(settings: dict[str, object], mode: str) -> bool:
  values = cast(dict[object, object], settings["settings"])
  destination = cast(str, values["service_config"])
  result = _run([*_command(settings, "read_config"), destination], capture=True)
  if result.returncode != 0 or result.stdout is None:
    return False
  try:
    config = json.loads(result.stdout)
  except json.JSONDecodeError:
    return False
  if not isinstance(config, dict):
    return False
  config[cast(str, values["mode_key"])] = mode
  if mode == values["integrated_mode"]:
    config[cast(str, values["vfio_enable_key"])] = values["vfio_enable_value"]
  serialized = json.dumps(config, indent=cast(int, values["json_indent"])) + "\n"
  return _install_root_content(settings, serialized, destination, cast(str, values["service_config_mode"]))


def _enable_hybrid(settings: dict[str, object]) -> int:
  values = cast(dict[object, object], settings["settings"])
  result = _run(
    [*_command(settings, "sudo"), *_command(settings, "remove"), cast(str, values["sleep_hook_destination"])]
  )
  if result.returncode != 0:
    return result.returncode
  result = _run(
    [*_command(settings, "sudo"), *_command(settings, "remove"), cast(str, values["startup_delay_destination"])]
  )
  if result.returncode != 0:
    return result.returncode
  return _run(_command(settings, "reboot")).returncode


def _enable_integrated(settings: dict[str, object]) -> int:
  root = cast(Path, settings["root"])
  values = cast(dict[object, object], settings["settings"])
  directories = ("drop_in_directory", "sleep_hook_directory")
  for name in directories:
    if _run([*_command(settings, "sudo"), *_command(settings, "make_directory"), cast(str, values[name])]).returncode != 0:
      return 1
  installations = (
    ("startup_delay_source", "startup_delay_destination", "startup_delay_mode", "startup_delay_install_failed"),
    ("sleep_hook_source", "sleep_hook_destination", "sleep_hook_mode", "sleep_hook_install_failed"),
  )
  messages = cast(dict[object, object], settings["messages"])
  for source_key, destination_key, mode_key, message_key in installations:
    if not _install_root_file(
      settings,
      root / cast(str, values[source_key]),
      cast(str, values[destination_key]),
      cast(str, values[mode_key]),
    ):
      print(messages[message_key], file=sys.stderr)
      return 1
  if not _switch(settings, cast(str, values["integrated_mode"])):
    return 1
  return _run(_command(settings, "reboot")).returncode


def main(arguments: list[str]) -> int:
  settings: dict[str, object] = {}
  try:
    settings = _settings()
    values = cast(dict[object, object], settings["settings"])
    messages = cast(dict[object, object], settings["messages"])
    if _run(_command(settings, "package_missing")).returncode == 0:
      if _run(_command(settings, "install_package")).returncode != 0:
        return 1
      if not _write_service_config(settings):
        return 1
      if _run([*_command(settings, "sudo"), *_command(settings, "enable_service")]).returncode != 0:
        return 1
    mode = _query_mode(settings)
    if mode is None:
      print(messages["unavailable"], file=sys.stderr)
      return 1
    if mode == values["integrated_mode"]:
      if _confirm(settings, "enable_dedicated"):
        if not _switch(settings, cast(str, values["hybrid_mode"])):
          return 1
        return _enable_hybrid(settings)
      return 0
    if mode == values["hybrid_mode"]:
      if _confirm(settings, "use_integrated"):
        return _enable_integrated(settings)
      return 0
    print(messages["unknown_mode"], file=sys.stderr)
    return 1
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError):
    messages = cast(dict[object, object], settings.get("messages", {}))
    if isinstance(messages.get("invalid_configuration"), str):
      print(messages["invalid_configuration"], file=sys.stderr)
    return os.EX_CONFIG
