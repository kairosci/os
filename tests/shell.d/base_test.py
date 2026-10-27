"""Shared path discovery, isolated environment, and TAP helpers."""

from __future__ import annotations

import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_environment(**updates: str) -> dict[str, str]:
  environment = os.environ.copy()
  environment["ROOT"] = str(ROOT)
  environment["ARCH_PATH"] = str(ROOT)
  environment["PATH"] = f"{ROOT / 'src/commands'}:{environment.get('PATH', '')}"
  environment["ARCH_LANGUAGE_FILE"] = str(ROOT / "tests/.no-language")
  for name in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"):
    environment.pop(name, None)
  environment.update({key: str(value) for key, value in updates.items()})
  return environment


def pass_check(description: str) -> None:
  print(f"ok - {description}")


def fail_check(description: str) -> None:
  print(f"not ok - {description}", file=sys.stderr)
  raise SystemExit(1)
