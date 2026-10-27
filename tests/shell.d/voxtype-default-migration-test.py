"""Preserve the selected dictation backend without overwriting user choices."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1791479273.py"


class VoxtypeDefaultMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="voxtype-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.home = Path(self.temporary.name)
    self.bin_dir = self.home / "bin"
    self.bin_dir.mkdir()
    self.log = self.home / "calls"
    self.write_command("arch-i18n", 'printf "i18n:%s\\n" "$1" >>"$TEST_LOG"\n')
    self.write_command(
      "arch-pkg-present",
      'printf "package:%s\\n" "$1" >>"$TEST_LOG"\n'
      '[[ ${TEST_PACKAGE_INSTALLED:-1} == 1 ]]\n',
    )

  def write_command(self, name: str, body: str) -> None:
    command = self.bin_dir / name
    command.write_text(f"#!/bin/bash\nset -euo pipefail\n{body}", encoding="utf-8")
    command.chmod(0o755)

  def run_migration(self, **updates: str) -> subprocess.CompletedProcess[str]:
    environment = test_environment(
      ARCH_PATH=str(ROOT),
      HOME=str(self.home),
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
      TEST_LOG=str(self.log),
      **updates,
    )
    return subprocess.run(
      ["python3", "-I", str(MIGRATION)],
      env=environment,
      check=False,
      capture_output=True,
      text=True,
    )

  def test_sets_default_for_installed_voxtype(self) -> None:
    result = self.run_migration()

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(
      (self.home / ".config/arch/defaults/dictation").read_text(encoding="utf-8"),
      "voxtype\n",
    )
    self.assertEqual(
      self.log.read_text(encoding="utf-8").splitlines(),
      ["i18n:migration.preserveVoxtypeDefault", "package:voxtype-bin"],
    )

  def test_keeps_custom_default_and_dangling_symlink(self) -> None:
    directory = self.home / ".config/arch/defaults"
    directory.mkdir(parents=True)
    config = directory / "dictation"
    config.write_text("custom-backend\n", encoding="utf-8")

    result = self.run_migration()

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(config.read_text(encoding="utf-8"), "custom-backend\n")
    self.assertEqual(self.log.read_text(encoding="utf-8").splitlines(), ["i18n:migration.preserveVoxtypeDefault"])

    config.unlink()
    config.symlink_to(self.home / "missing-backend")
    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertTrue(config.is_symlink())

  def test_does_not_set_default_without_voxtype(self) -> None:
    result = self.run_migration(TEST_PACKAGE_INSTALLED="0")

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse((self.home / ".config/arch/defaults/dictation").exists())


if __name__ == "__main__":
  unittest.main()
