"""Remove only links to retired Arch and app agent skills."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1793122575.py"


class AgentSkillShimMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="agent-skill-shim-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.home = self.scratch / "home"
    self.home.mkdir()
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    i18n = self.bin_dir / "arch-i18n"
    i18n.write_text("#!/usr/bin/python3 -I\nimport sys\nprint(sys.argv[1] + ':' + sys.argv[2])\n", encoding="utf-8")
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

  def test_removes_managed_links_and_preserves_user_content(self) -> None:
    arch_skills = self.home / ".agents/skills"
    claude_skills = self.home / ".claude/skills"
    hermes_skills = self.home / ".hermes/profiles/work/skills"
    for directory in (arch_skills, claude_skills, hermes_skills):
      directory.mkdir(parents=True)
    (arch_skills / "arch").symlink_to("/old/install/default/agents/skills/arch")
    (claude_skills / "diagnose-crash").symlink_to("/old/install/default/agents/skills/diagnose-crash")
    (hermes_skills / "app").symlink_to("/opt/application/assets/agent-skill/app")
    (claude_skills / "custom").symlink_to("/home/user/custom-skill")
    (claude_skills / "notes").write_text("keep", encoding="utf-8")

    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.removeManagedSkillLinks:3\n")
    self.assertFalse((arch_skills / "arch").is_symlink())
    self.assertFalse((claude_skills / "diagnose-crash").is_symlink())
    self.assertFalse((hermes_skills / "app").is_symlink())
    self.assertEqual(os.readlink(claude_skills / "custom"), "/home/user/custom-skill")
    self.assertEqual((claude_skills / "notes").read_text(encoding="utf-8"), "keep")

    repeated = self.run_migration()
    self.assertEqual(repeated.returncode, 0, repeated.stderr)
    self.assertEqual(repeated.stdout, "")

  def test_skips_a_skills_directory_linked_outside_home(self) -> None:
    outside = self.scratch / "outside"
    outside.mkdir()
    link = outside / "arch"
    link.symlink_to("/old/install/default/agents/skills/arch")
    (self.home / ".agents").mkdir()
    (self.home / ".agents/skills").symlink_to(outside, target_is_directory=True)

    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "")
    self.assertTrue(link.is_symlink())


if __name__ == "__main__":
  unittest.main()
