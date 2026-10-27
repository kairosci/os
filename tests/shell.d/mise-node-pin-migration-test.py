"""Update only the exact Node version pin from the offline setup."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1790457067.py"


class MiseNodePinMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="mise-node-pin-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.home = self.scratch / "home"
    self.config = self.home / ".config/mise/config.toml"
    self.config.parent.mkdir(parents=True)
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    i18n = self.bin_dir / "arch-i18n"
    i18n.write_text("#!/usr/bin/python3 -I\nimport sys\nprint(sys.argv[1])\n", encoding="utf-8")
    i18n.chmod(0o755)
    self.environment = test_environment(
      HOME=self.home,
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
    )

  def run_migration(self) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      ["/usr/bin/python3", "-I", str(MIGRATION)],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
    )

  def test_replaces_only_exact_semver_pin_and_preserves_mode(self) -> None:
    self.config.write_text(
      '[tools]\nnode = "22.12.0"\nruby = "3.4.1"\nnode = "22"\n',
      encoding="utf-8",
    )
    self.config.chmod(0o640)

    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.loosenOfflineNodePin\n")
    self.assertEqual(
      self.config.read_text(encoding="utf-8"),
      '[tools]\nnode = "latest"\nruby = "3.4.1"\nnode = "22"\n',
    )
    self.assertEqual(self.config.stat().st_mode & 0o777, 0o640)

  def test_replaces_a_symlink_like_sed_in_place_and_keeps_its_target(self) -> None:
    target = self.scratch / "mise-config.toml"
    target.write_text('node = "20.1.0"\n', encoding="utf-8")
    self.config.unlink(missing_ok=True)
    self.config.symlink_to(target)

    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(self.config.is_symlink())
    self.assertEqual(self.config.read_text(encoding="utf-8"), 'node = "latest"\n')
    self.assertEqual(target.read_text(encoding="utf-8"), 'node = "20.1.0"\n')

  def test_missing_config_is_a_no_op(self) -> None:
    self.config.unlink(missing_ok=True)
    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(self.config.exists())


if __name__ == "__main__":
  unittest.main()
