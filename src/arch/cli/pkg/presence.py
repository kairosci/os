from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

import yaml


class PackagePresenceSettings(TypedDict):
  command: str
  query_arguments: list[str]
  maximum_packages: int
  timeout_seconds: int
  statuses: dict[str, int]
  error_message: str


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, Mapping):
    raise TypeError(f"invalid package presence configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str) or not value:
    raise TypeError(f"invalid package presence configuration: {label} must be a non-empty string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid package presence configuration: {label} must be an integer")
  return value


def _settings() -> PackagePresenceSettings:
  root = Path(os.environ["AP"])
  raw: object = yaml.safe_load((root / "data/cli/pkg-presence.yml").read_text(encoding="utf-8"))
  settings = _mapping(raw, "root")
  query_arguments = settings.get("query_arguments")
  if not isinstance(query_arguments, list) or not all(isinstance(argument, str) for argument in query_arguments):
    raise TypeError("invalid package presence configuration: query_arguments must be a string list")
  timeout_seconds = _integer(settings.get("timeout_seconds"), "timeout_seconds")
  if timeout_seconds < 1:
    raise ValueError("invalid package presence configuration: timeout_seconds must be positive")
  maximum_packages = _integer(settings.get("maximum_packages"), "maximum_packages")
  if maximum_packages < 1:
    raise ValueError("invalid package presence configuration: maximum_packages must be positive")
  raw_statuses = _mapping(settings.get("statuses"), "statuses")
  statuses = {
    name: _integer(status, f"statuses.{name}")
    for name, status in raw_statuses.items()
    if isinstance(name, str)
  }
  if len(statuses) != len(raw_statuses):
    raise TypeError("invalid package presence configuration: status names must be strings")
  required_statuses = (
    "present_all_installed",
    "present_at_least_one_missing",
    "missing_at_least_one_missing",
    "missing_none_missing",
    "query_error",
  )
  if any(name not in statuses for name in required_statuses):
    raise ValueError("invalid package presence configuration: status mapping is incomplete")
  return {
    "command": _text(settings.get("command"), "command"),
    "query_arguments": query_arguments,
    "maximum_packages": maximum_packages,
    "timeout_seconds": timeout_seconds,
    "statuses": statuses,
    "error_message": _text(settings.get("error_message"), "error_message"),
  }


def _package_installed(settings: PackagePresenceSettings, package: str, timeout_seconds: float) -> bool:
  result = subprocess.run(
    [settings["command"], *settings["query_arguments"], package],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    timeout=timeout_seconds,
    check=False,
  )
  return result.returncode == 0


def _run(packages: Sequence[str], *, check_missing: bool) -> int:
  if packages and packages[0] == "--":
    packages = packages[1:]
  try:
    settings = _settings()
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load package presence configuration: {error}", file=sys.stderr)
    return 2
  try:
    if len(packages) > settings["maximum_packages"]:
      raise ValueError("too many package names")
    deadline = time.monotonic() + settings["timeout_seconds"]
    states = []
    for package in packages:
      remaining = deadline - time.monotonic()
      if remaining <= 0:
        raise subprocess.TimeoutExpired(settings["command"], settings["timeout_seconds"])
      states.append(_package_installed(settings, package, remaining))
  except (OSError, subprocess.SubprocessError, ValueError) as error:
    print(settings["error_message"].format(error=error), file=sys.stderr)
    return settings["statuses"]["query_error"]
  statuses = settings["statuses"]
  if check_missing:
    return (
      statuses["missing_at_least_one_missing"]
      if any(not state for state in states)
      else statuses["missing_none_missing"]
    )
  return (
    statuses["present_all_installed"]
    if all(states)
    else statuses["present_at_least_one_missing"]
  )


def present_main(packages: list[str]) -> int:
  return _run(packages, check_missing=False)


def missing_main(packages: list[str]) -> int:
  return _run(packages, check_missing=True)
