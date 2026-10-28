from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

import yaml


def load_config() -> dict[str, Any]:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/cli/update-available.yml").read_text(encoding="utf-8"))
  if not isinstance(config, dict):
    raise ValueError("invalid update availability configuration")
  return config


def run(command: list[str], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
  return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def checkout_updates(config: dict[str, Any], arch_path: str) -> list[str]:
  checkout = config["checkout"]
  if arch_path == checkout["system_path"]:
    return []

  upstream_result = run([*checkout["git"], "-C", arch_path, *checkout["upstream_args"]])
  upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else ""
  if not upstream:
    return []

  try:
    run(
      [*checkout["git"], "-C", arch_path, *checkout["fetch_args"]],
      timeout=int(checkout["fetch_timeout_seconds"]),
    )
    behind_result = run(
      [*checkout["git"], "-C", arch_path, *checkout["behind_args"], upstream]
    )
  except (OSError, subprocess.TimeoutExpired):
    return []

  try:
    behind = int(behind_result.stdout.strip()) if behind_result.returncode == 0 else 0
  except ValueError:
    behind = 0
  if behind <= 0:
    return []

  message = run([
    *config["commands"]["i18n"], "--count", str(behind),
    config["messages"]["checkout"], str(behind), upstream,
  ])
  return [message.stdout.rstrip("\n")]


def main() -> int:
  try:
    config = load_config()
    updates = checkout_updates(config, os.environ["ARCH_PATH"])
    result = run(config["commands"]["checkupdates"])
    if result.returncode == int(config["statuses"]["updates_available"]):
      updates.extend(line for line in result.stdout.splitlines() if line.strip())

    if updates:
      print("\n".join(updates))
      return int(config["statuses"]["updates_available"])

    localized = run([*config["commands"]["i18n"], config["messages"]["up_to_date"]])
    print(localized.stdout.rstrip("\n"))
    return int(config["statuses"]["no_updates"])
  except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError):
    return int(config["statuses"]["failed"]) if isinstance(locals().get("config"), dict) else 2


if __name__ == "__main__":
  raise SystemExit(main())
