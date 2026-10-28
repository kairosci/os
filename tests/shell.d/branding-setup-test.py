"""Verify branding setup reports broken settings without exposing a traceback."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from base_test import ROOT, fail_check, pass_check, test_environment

SETUP = ROOT / "src/arch/python/installer/system_setup/branding.py"


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary_directory:
    invalid_root = Path(temporary_directory)
    config_directory = invalid_root / "data/installer"
    config_directory.mkdir(parents=True)
    (config_directory / "branding-setup.yml").write_text("branding: [\n", encoding="utf-8")
    result = subprocess.run(
      ["python3", "-I", str(SETUP)],
      check=False,
      env=test_environment(ARCH_PATH=str(invalid_root)),
      capture_output=True,
      text=True,
    )
    if result.returncode != 78:
      fail_check("branding setup reports malformed configuration at its command boundary")
    if "Could not load branding setup configuration" not in result.stderr or "Traceback" in result.stderr:
      fail_check("branding setup explains malformed configuration without a traceback")
    pass_check("branding setup handles malformed YAML at its command boundary")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
