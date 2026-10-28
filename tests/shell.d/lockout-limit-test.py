"""Verify the PAM lockout setup keeps file safety checks and errors bounded."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from base_test import ROOT, fail_check, pass_check, test_environment

SETUP = ROOT / "src/arch/python/installer/system_setup/lockout_limit.py"


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary_directory:
    temporary = Path(temporary_directory)
    invalid_root = temporary / "invalid"
    config_directory = invalid_root / "data/installer"
    config_directory.mkdir(parents=True)
    (config_directory / "config-setup.yml").write_text("lockout_limit: [\n", encoding="utf-8")
    result = subprocess.run(
      ["python3", "-I", str(SETUP)],
      check=False,
      env=test_environment(ARCH_PATH=str(invalid_root)),
      capture_output=True,
      text=True,
    )
    if result.returncode != 78:
      fail_check("lockout setup reports malformed configuration at its command boundary")
    if "Could not load lockout limit configuration" not in result.stderr or "Traceback" in result.stderr:
      fail_check("lockout setup explains malformed configuration without a traceback")
    pass_check("lockout setup handles malformed YAML at its command boundary")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
