"""Shared path discovery, isolated environment, and TAP helpers."""

from __future__ import annotations

import os
import fcntl
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CLI_STAGE = ROOT / "build/test-cli-entrypoints"
CLI_BIN = CLI_STAGE / "usr/share/arch/src/arch/commands"


def ensure_cli_entrypoints() -> Path:
  lock_path = ROOT / "build/test-cli-entrypoints.lock"
  lock_path.parent.mkdir(parents=True, exist_ok=True)
  with lock_path.open("a", encoding="utf-8") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    marker = CLI_BIN / "archctl"
    if (
      not marker.is_file()
      or (ROOT / "scripts/cli_entrypoints.py").stat().st_mtime_ns > marker.stat().st_mtime_ns
      or (ROOT / "data/cli/python-entrypoints.yml").stat().st_mtime_ns > marker.stat().st_mtime_ns
      or (ROOT / "data/cli/groups.yml").stat().st_mtime_ns > marker.stat().st_mtime_ns
    ):
      subprocess.run(
        ["python3", str(ROOT / "scripts/cli_entrypoints.py"), "generate", "--destination", str(CLI_STAGE)],
        check=True,
      )
  return CLI_BIN


CLI_BIN = ensure_cli_entrypoints()


def test_environment(**updates: str) -> dict[str, str]:
  environment = os.environ.copy()
  environment["ROOT"] = str(ROOT)
  environment["AP"] = str(ROOT)
  environment["PATH"] = f"{CLI_BIN}:{ROOT / 'src/arch/commands'}:{environment.get('PATH', '')}"
  environment["ARCH_LANGUAGE_FILE"] = str(ROOT / "tests/.no-language")
  for name in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"):
    environment.pop(name, None)
  if "PATH" in updates:
    updates["PATH"] = f"{CLI_BIN}:{ROOT / 'src/arch/commands'}:{updates['PATH']}"
  environment.update({key: str(value) for key, value in updates.items()})
  return environment


def pass_check(description: str) -> None:
  print(f"ok - {description}")


def fail_check(description: str) -> None:
  print(f"not ok - {description}", file=sys.stderr)
  raise SystemExit(1)
