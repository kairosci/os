"""Install the Arch session entry and remove obsolete session names."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1792868000.py"


class WaylandSessionMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="wayland-session-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.session_dir = self.scratch / "sessions"
    self.session_dir.mkdir()
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    i18n = self.bin_dir / "arch-i18n"
    i18n.write_text("#!/usr/bin/python3 -I\nimport sys\nprint(sys.argv[1])\n", encoding="utf-8")
    i18n.chmod(0o755)
    sudo = self.bin_dir / "sudo"
    sudo.write_text(
      "#!/usr/bin/python3 -I\n"
      "import os, sys\n"
      "os.execvpe(sys.argv[1], sys.argv[1:], os.environ)\n",
      encoding="utf-8",
    )
    sudo.chmod(0o755)
    self.environment = test_environment(
      ARCH_WAYLAND_SESSIONS_DIR=self.session_dir,
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
    )

  def run_migration(self, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      ["/usr/bin/python3", "-I", str(MIGRATION)],
      check=False,
      capture_output=True,
      text=True,
      env=environment or self.environment,
    )

  def test_installs_arch_entry_removes_obsolete_names_and_is_idempotent(self) -> None:
    target = self.session_dir / "arch.desktop"
    obsolete = self.session_dir / "legacyarchy.desktop"
    target.write_text("old session\n", encoding="utf-8")
    obsolete.write_text("old name\n", encoding="utf-8")

    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("Name=Arch Linux (Hyprland)", target.read_text(encoding="utf-8"))
    self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o644)
    self.assertFalse(obsolete.exists())

    repeated = self.run_migration()
    self.assertEqual(repeated.returncode, 0, repeated.stderr)

  def test_missing_source_fails_before_touching_session_entries(self) -> None:
    incomplete_root = self.scratch / "incomplete"
    config_dir = incomplete_root / "data/migrations"
    config_dir.mkdir(parents=True)
    shutil.copy2(ROOT / "data/migrations/1792868000.yml", config_dir)
    existing = self.session_dir / "legacyarchy.desktop"
    existing.write_text("keep until source exists\n", encoding="utf-8")
    environment = self.environment | {"ARCH_PATH": str(incomplete_root)}

    result = self.run_migration(environment)
    self.assertEqual(result.returncode, 1)
    self.assertEqual(result.stderr, "migration.archSessionEntryMissing\n")
    self.assertEqual(existing.read_text(encoding="utf-8"), "keep until source exists\n")


if __name__ == "__main__":
  unittest.main()
