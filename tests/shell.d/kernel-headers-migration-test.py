"""Install headers only for kernel packages present on the system."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1789444024.py"


class KernelHeadersMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="kernel-headers-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.home = Path(self.temporary.name)
    self.bin_dir = self.home / "bin"
    self.bin_dir.mkdir()
    self.log = self.home / "calls"
    self.write_command("arch-i18n", 'printf "i18n:%s\\n" "$1" >>"$TEST_LOG"\n')
    self.write_command(
      "arch-pkg-present",
      'printf "present:%s\\n" "$1" >>"$TEST_LOG"\n'
      'case " ${TEST_INSTALLED_PACKAGES:-} " in *" $1 "*) exit 0 ;; esac\n'
      "exit 1\n",
    )
    self.write_command("arch-pkg-add", 'printf "add:%s\\n" "$*" >>"$TEST_LOG"\n')

  def write_command(self, name: str, body: str) -> None:
    command = self.bin_dir / name
    command.write_text(f"#!/bin/bash\nset -euo pipefail\n{body}", encoding="utf-8")
    command.chmod(0o755)

  def run_migration(self, installed: str = "") -> subprocess.CompletedProcess[str]:
    environment = test_environment(
      ARCH_PATH=str(ROOT),
      HOME=str(self.home),
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
      TEST_LOG=str(self.log),
      TEST_INSTALLED_PACKAGES=installed,
    )
    return subprocess.run(
      ["python3", "-I", str(MIGRATION)],
      env=environment,
      check=False,
      capture_output=True,
      text=True,
    )

  def test_adds_headers_for_installed_kernels_only(self) -> None:
    result = self.run_migration("linux linux-t2")

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(
      self.log.read_text(encoding="utf-8").splitlines(),
      [
        "i18n:migration.installKernelHeaders",
        "present:linux",
        "add:linux-headers",
        "present:linux-t2",
        "add:linux-t2-headers",
      ],
    )

  def test_skips_header_install_when_no_supported_kernel_is_installed(self) -> None:
    result = self.run_migration()

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(
      self.log.read_text(encoding="utf-8").splitlines(),
      ["i18n:migration.installKernelHeaders", "present:linux", "present:linux-t2"],
    )


if __name__ == "__main__":
  unittest.main()
