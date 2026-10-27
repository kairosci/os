"""Verify the T2 package repository rejects unsigned package payloads."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1793121678.py"
REPOSITORY_SETUP = ROOT / "src/python/installer/hardware/pacman_repositories.py"


class T2RepositorySignatureTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="t2-repository-signature-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.config = self.scratch / "pacman.conf"
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    self._write_stub(
      "lspci",
      "import sys\n"
      "print('00:00.0 Apple Inc. T2 [106b:1801]')\n",
    )
    self._write_stub(
      "arch-i18n",
      "import sys\n"
      "print(sys.argv[1])\n",
    )
    self._write_stub(
      "sudo",
      "import os, sys\n"
      "os.execv('/usr/bin/' + sys.argv[1], ['/usr/bin/' + sys.argv[1], *sys.argv[2:]])\n",
    )
    self.environment = test_environment(
      ARCH_PACMAN_CONFIG_PATH=self.config,
      PATH=f"{self.bin_dir}:{ROOT / 'src/cli'}:{os.environ.get('PATH', '')}",
    )

  def test_new_config_requires_signatures_and_existing_never_is_migrated(self) -> None:
    self.config.write_text("[options]\nSigLevel = Required DatabaseOptional\n", encoding="utf-8")
    setup = subprocess.run(
      ["/usr/bin/python3", "-I", str(REPOSITORY_SETUP)],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
    )
    self.assertEqual(setup.returncode, 0, setup.stderr)
    self.assertIn("SigLevel = PackageRequired", self.config.read_text(encoding="utf-8"))

    original = (
      "[options]\nSigLevel = Required DatabaseOptional\n\n"
      "[arch-mact2]\nServer = https://invalid.example/\nSigLevel = Never\n\n"
      "[local-test]\nSigLevel = Never\n"
    )
    self.config.write_text(original, encoding="utf-8")
    migration = self._run_migration()
    self.assertEqual(migration.returncode, 0, migration.stderr)
    self.assertEqual(migration.stdout, "migration.requireT2PackageSignatures\n")
    updated = self.config.read_text(encoding="utf-8")
    self.assertIn("[arch-mact2]\nServer = https://invalid.example/\nSigLevel = PackageRequired", updated)
    self.assertIn("[local-test]\nSigLevel = Never", updated)

    optional = updated.replace(
      "SigLevel = PackageRequired",
      "SigLevel = PackageOptional DatabaseRequired",
      1,
    )
    self.config.write_text(optional, encoding="utf-8")
    hardened = self._run_migration()
    self.assertEqual(hardened.returncode, 0, hardened.stderr)
    self.assertEqual(hardened.stdout, "migration.requireT2PackageSignatures\n")
    updated_again = self.config.read_text(encoding="utf-8")
    self.assertIn("SigLevel = PackageRequired", updated_again)
    self.assertNotIn("PackageOptional", updated_again)

    repeated = self._run_migration()
    self.assertEqual(repeated.returncode, 0, repeated.stderr)
    self.assertEqual(repeated.stdout, "")
    self.assertEqual(self.config.read_text(encoding="utf-8"), updated_again)

  def test_migration_refuses_a_symlinked_pacman_config(self) -> None:
    target = self.scratch / "target.conf"
    target.write_text("[arch-mact2]\nSigLevel = Never\n", encoding="utf-8")
    self.config.symlink_to(target)
    result = self._run_migration()
    self.assertEqual(result.returncode, 1)
    self.assertEqual(target.read_text(encoding="utf-8"), "[arch-mact2]\nSigLevel = Never\n")

    self.config.unlink()
    self.config.symlink_to(self.scratch / "missing.conf")
    broken = self._run_migration()
    self.assertEqual(broken.returncode, 1)

  def _run_migration(self) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      ["/usr/bin/python3", "-I", str(MIGRATION)],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
    )

  def _write_stub(self, name: str, source: str) -> None:
    path = self.bin_dir / name
    path.write_text(f"#!/usr/bin/python3 -I\n{source}", encoding="utf-8")
    path.chmod(0o700)


if __name__ == "__main__":
  unittest.main()
