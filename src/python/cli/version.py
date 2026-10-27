from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  settings = yaml.safe_load((root / "data/cli/version.yml").read_text(encoding="utf-8"))
  if not isinstance(settings, dict):
    raise ValueError("invalid version command configuration")
  return settings


def _output(command: list[str]) -> tuple[int, str]:
  result = subprocess.run(command, check=False, capture_output=True, text=True)
  return result.returncode, result.stdout.strip()


def version_main() -> int:
  settings = _settings()
  root = Path(os.environ["ARCH_PATH"])
  version = settings["version"]
  packaged_root = os.environ.get(
    settings["commands"]["packaged_root_environment"],
    settings["commands"]["packaged_root_default"],
  )
  if str(root).rstrip("/") != str(packaged_root).rstrip("/"):
    status, commit = _output([argument.format(path=str(root)) for argument in settings["commands"]["git_hash"]])
    if status == 0 and commit:
      print(version["development_hash_template"].format(hash=commit))
    else:
      print(version["development_label"])
    return 0

  for package in version["package_names"]:
    status, output = _output([*settings["commands"]["package_query"], package])
    fields = output.split()
    if status == 0 and len(fields) > 1:
      print(fields[1])
      return 0
  return int(version["missing_package_status"])


def version_branch_main() -> int:
  settings = _settings()
  root = Path(os.environ["ARCH_PATH"])
  commands = settings["commands"]
  packaged_root = os.environ.get(
    commands["packaged_root_environment"],
    commands["packaged_root_default"],
  )
  if str(root).rstrip("/") == str(packaged_root).rstrip("/"):
    return int(settings["version"]["branch_empty_status"])

  status, branch = _output([argument.format(path=str(root)) for argument in commands["git_branch"]])
  if status == 0 and branch:
    print(branch)
    return 0
  status, commit = _output([argument.format(path=str(root)) for argument in commands["git_hash"]])
  if status != 0 or not commit:
    return int(settings["version"]["branch_empty_status"])
  print(settings["version"]["detached_branch_template"].format(hash=commit))
  return 0


def version_channel_main() -> int:
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
