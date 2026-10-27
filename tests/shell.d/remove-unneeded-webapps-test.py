"""Remove only the shipped HEY and Basecamp launchers from existing users."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1793141000.py"
CONFIG = yaml.safe_load((ROOT / "data/migrations/1793141000.yml").read_text(encoding="utf-8"))


class RemoveUnneededWebappsTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="remove-webapps-")
    self.addCleanup(self.temporary.cleanup)
    self.home = Path(self.temporary.name)
    self.applications = self.home / CONFIG["paths"]["applications"]
    self.applications.mkdir(parents=True)

  def run_migration(self) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      ["python3", "-I", str(MIGRATION)],
      env=test_environment(ARCH_PATH=str(ROOT), HOME=str(self.home)),
      check=False,
      capture_output=True,
      text=True,
    )

  def test_removes_shipped_launchers_and_only_hey_mailto_default(self) -> None:
    basecamp, hey = CONFIG["launchers"]
    (self.applications / basecamp["name"]).write_text(basecamp["content"], encoding="utf-8")
    custom = self.applications / "HEY.desktop"
    custom.write_text(hey["content"] + "X-User-Changed=true\n", encoding="utf-8")
    mime_file = self.home / ".config/mimeapps.list"
    mime_file.parent.mkdir()
    mime_file.write_text(
      "[Default Applications]\nx-scheme-handler/mailto=HEY.desktop;custom-mail.desktop;\n",
      encoding="utf-8",
    )

    result = self.run_migration()

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse((self.applications / "Basecamp.desktop").exists())
    self.assertTrue(custom.exists())
    self.assertEqual(
      mime_file.read_text(encoding="utf-8"),
      "[Default Applications]\nx-scheme-handler/mailto=custom-mail.desktop;\n",
    )

  def test_removes_exact_hey_launcher(self) -> None:
    hey = CONFIG["launchers"][1]
    launcher = self.applications / hey["name"]
    launcher.write_text(hey["content"], encoding="utf-8")

    result = self.run_migration()

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(launcher.exists())

  def test_preserves_symlinked_launcher_and_is_idempotent(self) -> None:
    launcher = self.applications / CONFIG["launchers"][0]["name"]
    target = self.home / "custom.desktop"
    target.write_text(CONFIG["launchers"][0]["content"], encoding="utf-8")
    launcher.symlink_to(target)

    first = self.run_migration()
    second = self.run_migration()

    self.assertEqual(first.returncode, 0, first.stderr)
    self.assertEqual(second.returncode, 0, second.stderr)
    self.assertTrue(launcher.is_symlink())


if __name__ == "__main__":
  unittest.main()
