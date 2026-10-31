"""Restart an application through the user session launcher."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import yaml


class RestartSettings(TypedDict):
  minimum_arguments: int
  stop_timeout_seconds: int
  stop_application: list[str]
  launch_application: list[str]
  signal_application: list[str]
  process_presence: list[str]
  tmux_has_session: list[str]
  tmux_source_file: list[str]
  output_discard: str
  config_home_environment: str
  home_environment: str
  default_config_home: str
  tmux_config_relative: str
  hyprsunset: str
  btop: str
  helix: str
  btop_signal: str
  helix_signal: str
  usage: str
  launch_error: str
  success: int
  invalid_arguments: int
  operation_failed: int
  process_not_found: int


def _mapping(value: object, error_message: str) -> dict[str, object]:
  if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
    raise ValueError(error_message)
  return cast(dict[str, object], value)


def _text(value: object, error_message: str) -> str:
  if not isinstance(value, str) or not value:
    raise ValueError(error_message)
  return value


def _strings(value: object, error_message: str) -> list[str]:
  if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
    raise ValueError(error_message)
  return cast(list[str], value)


def _integer(value: object, error_message: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool) or value < 0:
    raise ValueError(error_message)
  return value


def _positive_integer(value: object, error_message: str) -> int:
  result = _integer(value, error_message)
  if result == 0:
    raise ValueError(error_message)
  return result


def _settings() -> RestartSettings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/restart-app.yml").read_text(encoding="utf-8"))
  if not isinstance(raw, dict):
    raise TypeError()
  raw_messages = raw.get("messages")
  if not isinstance(raw_messages, dict):
    raise TypeError()
  configuration_error = raw_messages.get("configuration_error")
  if not isinstance(configuration_error, str) or not configuration_error:
    raise ValueError()
  document = _mapping(raw, configuration_error)
  limits = _mapping(document.get("limits"), configuration_error)
  commands = _mapping(document.get("commands"), configuration_error)
  paths = _mapping(document.get("paths"), configuration_error)
  applications = _mapping(document.get("applications"), configuration_error)
  signals = _mapping(document.get("signals"), configuration_error)
  messages = _mapping(document.get("messages"), configuration_error)
  statuses = _mapping(document.get("statuses"), configuration_error)
  return {
    "minimum_arguments": _positive_integer(limits.get("minimum_arguments"), configuration_error),
    "stop_timeout_seconds": _positive_integer(limits.get("stop_timeout_seconds"), configuration_error),
    "stop_application": _strings(commands.get("stop_application"), configuration_error),
    "launch_application": _strings(commands.get("launch_application"), configuration_error),
    "signal_application": _strings(commands.get("signal_application"), configuration_error),
    "process_presence": _strings(commands.get("process_presence"), configuration_error),
    "tmux_has_session": _strings(commands.get("tmux_has_session"), configuration_error),
    "tmux_source_file": _strings(commands.get("tmux_source_file"), configuration_error),
    "output_discard": _text(paths.get("output_discard"), configuration_error),
    "config_home_environment": _text(paths.get("config_home_environment"), configuration_error),
    "home_environment": _text(paths.get("home_environment"), configuration_error),
    "default_config_home": _text(paths.get("default_config_home"), configuration_error),
    "tmux_config_relative": _text(paths.get("tmux_config_relative"), configuration_error),
    "hyprsunset": _text(applications.get("hyprsunset"), configuration_error),
    "btop": _text(applications.get("btop"), configuration_error),
    "helix": _text(applications.get("helix"), configuration_error),
    "btop_signal": _text(signals.get("btop"), configuration_error),
    "helix_signal": _text(signals.get("helix"), configuration_error),
    "usage": _text(messages.get("usage"), configuration_error),
    "launch_error": _text(messages.get("launch_error"), configuration_error),
    "success": _integer(statuses.get("success"), configuration_error),
    "invalid_arguments": _integer(statuses.get("invalid_arguments"), configuration_error),
    "operation_failed": _integer(statuses.get("operation_failed"), configuration_error),
    "process_not_found": _integer(statuses.get("process_not_found"), configuration_error),
  }


def _load_settings() -> RestartSettings | None:
  try:
    return _settings()
  except (KeyError, OSError, TypeError, UnicodeError, ValueError, yaml.YAMLError) as error:
    print(f"{error}", file=sys.stderr)
    return None


def _restart(arguments: list[str], settings: RestartSettings) -> int:
  if len(arguments) < settings["minimum_arguments"] or not arguments[0]:
    print(settings["usage"], file=sys.stderr)
    return settings["invalid_arguments"]
  try:
    subprocess.run(
      [*settings["stop_application"], arguments[0]],
      check=False,
      timeout=settings["stop_timeout_seconds"],
    )
    with open(settings["output_discard"], "wb") as output:
      subprocess.Popen(
        [*settings["launch_application"], *arguments],
        stdout=output,
        stderr=output,
      )
  except (OSError, subprocess.SubprocessError) as error:
    print(f"{settings['launch_error']}: {error}", file=sys.stderr)
    return settings["operation_failed"]
  return settings["success"]


def restart_app_main(arguments: list[str]) -> int:
  settings = _load_settings()
  if settings is None:
    return 1
  return _restart(arguments, settings)


def restart_hyprsunset_main() -> int:
  settings = _load_settings()
  if settings is None:
    return 1
  return _restart([settings["hyprsunset"]], settings)


def _run_action(command: list[str], settings: RestartSettings, quiet: bool = False) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    command,
    check=False,
    stdout=subprocess.DEVNULL if quiet else None,
    stderr=subprocess.DEVNULL if quiet else None,
    timeout=settings["stop_timeout_seconds"],
    text=True,
  )


def _action_settings() -> RestartSettings | None:
  settings = _load_settings()
  if settings is None:
    return None
  return settings


def restart_btop_main() -> int:
  settings = _action_settings()
  if settings is None:
    return 1
  command = [
    *settings["signal_application"],
    settings["btop_signal"],
    "-x",
    settings["btop"],
  ]
  try:
    result = _run_action(command, settings)
  except (OSError, subprocess.SubprocessError):
    return settings["operation_failed"]
  if result.returncode in (settings["success"], settings["process_not_found"]):
    return settings["success"]
  return settings["operation_failed"]


def restart_helix_main() -> int:
  settings = _action_settings()
  if settings is None:
    return 1
  try:
    present = _run_action(
      [*settings["process_presence"], settings["helix"]],
      settings,
      quiet=True,
    )
    if present.returncode != settings["success"]:
      return settings["success"]
    result = _run_action(
      [*settings["signal_application"], settings["helix_signal"], settings["helix"]],
      settings,
    )
  except (OSError, subprocess.SubprocessError):
    return settings["operation_failed"]
  return result.returncode


def restart_tmux_main() -> int:
  settings = _action_settings()
  if settings is None:
    return 1
  config_home = os.environ.get(settings["config_home_environment"])
  if config_home is None or config_home == "":
    config_home = str(Path(os.environ[settings["home_environment"]]) / settings["default_config_home"])
  config_file = Path(config_home) / settings["tmux_config_relative"]
  try:
    session = _run_action(settings["tmux_has_session"], settings, quiet=True)
    if session.returncode != settings["success"]:
      return settings["success"]
    result = _run_action([*settings["tmux_source_file"], str(config_file)], settings)
  except (OSError, subprocess.SubprocessError):
    return settings["operation_failed"]
  return result.returncode
