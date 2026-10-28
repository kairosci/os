from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

import yaml


class Commands(TypedDict):
  package_query: list[str]
  git_branch: list[str]
  git_hash: list[str]
  packaged_root_environment: str
  packaged_root_default: str


class Version(TypedDict):
  development_label: str
  development_hash_template: str
  branch_empty_status: int
  detached_branch_template: str
  package_names: list[str]
  missing_package_status: int


class MirrorPattern(TypedDict):
  channel: str
  pattern: str


class PackagePattern(TypedDict):
  channel: str
  text: str


class Channel(TypedDict):
  mirrorlist_environment: str
  mirrorlist_default: str
  config_environment: str
  config_default: str
  unknown: str
  mismatch_separator: str
  mirror_patterns: list[MirrorPattern]
  generic_mirror_patterns: list[str]
  package_patterns: list[PackagePattern]


class Settings(TypedDict):
  commands: Commands
  version: Version
  channel: Channel


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid version command configuration: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid version command configuration: {label} must be a string")
  return value


def _integer(value: object, label: str) -> int:
  if not isinstance(value, int) or isinstance(value, bool):
    raise TypeError(f"invalid version command configuration: {label} must be an integer")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list):
    raise TypeError(f"invalid version command configuration: {label} must be a list")
  return [_text(item, f"{label} item") for item in value]


def _mirror_patterns(value: object) -> list[MirrorPattern]:
  if not isinstance(value, list):
    raise TypeError("invalid version command configuration: channel.mirror_patterns must be a list")
  result: list[MirrorPattern] = []
  for index, item in enumerate(value):
    pattern = _mapping(item, f"channel.mirror_patterns[{index}]")
    channel = _text(pattern.get("channel"), f"channel.mirror_patterns[{index}].channel")
    expression = _text(pattern.get("pattern"), f"channel.mirror_patterns[{index}].pattern")
    try:
      re.compile(expression)
    except re.error as error:
      raise ValueError(f"invalid version command configuration: invalid mirror pattern {index}") from error
    result.append({"channel": channel, "pattern": expression})
  return result


def _package_patterns(value: object) -> list[PackagePattern]:
  if not isinstance(value, list):
    raise TypeError("invalid version command configuration: channel.package_patterns must be a list")
  result: list[PackagePattern] = []
  for index, item in enumerate(value):
    pattern = _mapping(item, f"channel.package_patterns[{index}]")
    result.append({
      "channel": _text(pattern.get("channel"), f"channel.package_patterns[{index}].channel"),
      "text": _text(pattern.get("text"), f"channel.package_patterns[{index}].text"),
    })
  return result


def _settings() -> Settings:
  root = Path(os.environ["ARCH_PATH"])
  raw: object = yaml.safe_load((root / "data/cli/version.yml").read_text(encoding="utf-8"))
  config = _mapping(raw, "root")
  commands = _mapping(config.get("commands"), "commands")
  version = _mapping(config.get("version"), "version")
  channel = _mapping(config.get("channel"), "channel")
  return {
    "commands": {
      "package_query": _text_list(commands.get("package_query"), "commands.package_query"),
      "git_branch": _text_list(commands.get("git_branch"), "commands.git_branch"),
      "git_hash": _text_list(commands.get("git_hash"), "commands.git_hash"),
      "packaged_root_environment": _text(commands.get("packaged_root_environment"), "commands.packaged_root_environment"),
      "packaged_root_default": _text(commands.get("packaged_root_default"), "commands.packaged_root_default"),
    },
    "version": {
      "development_label": _text(version.get("development_label"), "version.development_label"),
      "development_hash_template": _text(version.get("development_hash_template"), "version.development_hash_template"),
      "branch_empty_status": _integer(version.get("branch_empty_status"), "version.branch_empty_status"),
      "detached_branch_template": _text(version.get("detached_branch_template"), "version.detached_branch_template"),
      "package_names": _text_list(version.get("package_names"), "version.package_names"),
      "missing_package_status": _integer(version.get("missing_package_status"), "version.missing_package_status"),
    },
    "channel": {
      "mirrorlist_environment": _text(channel.get("mirrorlist_environment"), "channel.mirrorlist_environment"),
      "mirrorlist_default": _text(channel.get("mirrorlist_default"), "channel.mirrorlist_default"),
      "config_environment": _text(channel.get("config_environment"), "channel.config_environment"),
      "config_default": _text(channel.get("config_default"), "channel.config_default"),
      "unknown": _text(channel.get("unknown"), "channel.unknown"),
      "mismatch_separator": _text(channel.get("mismatch_separator"), "channel.mismatch_separator"),
      "mirror_patterns": _mirror_patterns(channel.get("mirror_patterns")),
      "generic_mirror_patterns": _text_list(channel.get("generic_mirror_patterns"), "channel.generic_mirror_patterns"),
      "package_patterns": _package_patterns(channel.get("package_patterns")),
    },
  }


def _output(command: list[str]) -> tuple[int, str]:
  result = subprocess.run(command, check=False, capture_output=True, text=True)
  return result.returncode, result.stdout.strip()


def _version_main() -> int:
  settings = _settings()
  root = Path(os.environ["ARCH_PATH"])
  version = settings["version"]
  commands = settings["commands"]
  packaged_root = os.environ.get(commands["packaged_root_environment"], commands["packaged_root_default"])
  if str(root).rstrip("/") != str(packaged_root).rstrip("/"):
    status, commit = _output([argument.format(path=str(root)) for argument in commands["git_hash"]])
    if status == 0 and commit:
      print(version["development_hash_template"].format(hash=commit))
    else:
      print(version["development_label"])
    return 0

  for package in version["package_names"]:
    status, output = _output([*commands["package_query"], package])
    fields = output.split()
    if status == 0 and len(fields) > 1:
      print(fields[1])
      return 0
  return version["missing_package_status"]


def _version_branch_main() -> int:
  settings = _settings()
  root = Path(os.environ["ARCH_PATH"])
  commands = settings["commands"]
  packaged_root = os.environ.get(commands["packaged_root_environment"], commands["packaged_root_default"])
  if str(root).rstrip("/") == str(packaged_root).rstrip("/"):
    return settings["version"]["branch_empty_status"]

  status, branch = _output([argument.format(path=str(root)) for argument in commands["git_branch"]])
  if status == 0 and branch:
    print(branch)
    return 0
  status, commit = _output([argument.format(path=str(root)) for argument in commands["git_hash"]])
  if status != 0 or not commit:
    return settings["version"]["branch_empty_status"]
  print(settings["version"]["detached_branch_template"].format(hash=commit))
  return 0


def _version_channel_main() -> int:
  settings = _settings()["channel"]
  mirrorlist = Path(os.environ.get(settings["mirrorlist_environment"]) or settings["mirrorlist_default"])
  pacman_config = Path(os.environ.get(settings["config_environment"]) or settings["config_default"])
  try:
    mirror_text = mirrorlist.read_text(encoding="utf-8", errors="replace")
  except OSError:
    mirror_text = ""
  try:
    package_text = pacman_config.read_text(encoding="utf-8", errors="replace")
  except OSError:
    package_text = ""

  mirror = next(
    (item["channel"] for item in settings["mirror_patterns"] if re.search(item["pattern"], mirror_text)),
    settings["unknown"],
  )
  package = next(
    (item["channel"] for item in settings["package_patterns"] if item["text"] in package_text),
    settings["unknown"],
  )
  if mirror == settings["unknown"] and package != settings["unknown"]:
    generic_mirror = any(re.search(pattern, mirror_text) for pattern in settings["generic_mirror_patterns"])
    if generic_mirror:
      mirror = package
  print(mirror if mirror == package else f"{mirror}{settings['mismatch_separator']}{package}")
  return 0


def _entry(operation: Callable[[], int], label: str) -> int:
  try:
    return operation()
  except (OSError, UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Could not load {label} configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  except (subprocess.SubprocessError, RuntimeError) as error:
    print(f"Could not determine {label}: {error}", file=sys.stderr)
    return os.EX_SOFTWARE


def version_main() -> int:
  return _entry(_version_main, "version")


def version_branch_main() -> int:
  return _entry(_version_branch_main, "version branch")


def version_channel_main() -> int:
  return _entry(_version_channel_main, "version channel")
