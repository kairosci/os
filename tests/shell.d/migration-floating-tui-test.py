"""Retire only the desktop launcher generated with the old floating TUI mode."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1793123682.py"
ENTRY = (
  "[Desktop Entry]\n"
  "Version=1.0\n"
  "Name=Disk Usage\n"
  "Comment=Disk Usage\n"
  "Exec=xdg-terminal-exec --app-id=TUI.float -e dua i\n"
  "Terminal=false\n"
  "Type=Application\n"
  "Icon=Disk Usage\n"
  "StartupNotify=true\n"
)


class FloatingTuiMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="floating-tui-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.data_home = self.scratch / "data"
    self.applications = self.data_home / "applications"
    self.applications.mkdir(parents=True)
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    i18n = self.bin_dir / "arch-i18n"
    i18n.write_text("#!/usr/bin/python3 -I\nimport sys\nprint(sys.argv[1])\n", encoding="utf-8")
    i18n.chmod(0o755)
    self.desktop_file = self.applications / "Disk Usage.desktop"
    self.environment = test_environment(
      XDG_DATA_HOME=self.data_home,
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

  def test_removes_exact_generated_floating_launcher_idempotently(self) -> None:
    self.desktop_file.write_text(ENTRY, encoding="utf-8")
    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.removeFloatingDiskUsageLauncher\n")
    self.assertFalse(self.desktop_file.exists())

    repeated = self.run_migration()
    self.assertEqual(repeated.returncode, 0, repeated.stderr)
    self.assertEqual(repeated.stdout, "")

  def test_preserves_customized_or_symlinked_desktop_entries(self) -> None:
    self.desktop_file.write_text(ENTRY.replace("Name=Disk Usage", "Name=Personal launcher"), encoding="utf-8")
    custom = self.run_migration()
    self.assertEqual(custom.returncode, 0, custom.stderr)
    self.assertEqual(custom.stdout, "")
    self.assertTrue(self.desktop_file.exists())

    self.desktop_file.unlink()
    target = self.scratch / "external.desktop"
    target.write_text(ENTRY, encoding="utf-8")
    self.desktop_file.symlink_to(target)
    linked = self.run_migration()
    self.assertEqual(linked.returncode, 0, linked.stderr)
    self.assertEqual(linked.stdout, "")
    self.assertTrue(self.desktop_file.is_symlink())
    self.assertEqual(target.read_text(encoding="utf-8"), ENTRY)


if __name__ == "__main__":
  unittest.main()
