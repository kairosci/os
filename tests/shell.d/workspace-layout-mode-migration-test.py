"""Convert saved workspace layout rules, then retire saved floating modes."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


class WorkspaceLayoutMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="workspace-layout-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.home = self.scratch / "home"
    self.home.mkdir()
    self.xdg_state = self.scratch / "state"
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    i18n = self.bin_dir / "arch-i18n"
    i18n.write_text("#!/usr/bin/python3 -I\nimport sys\nprint(sys.argv[1])\n", encoding="utf-8")
    i18n.chmod(0o755)
    self.environment = test_environment(
      HOME=self.home,
      XDG_STATE_HOME=self.xdg_state,
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
    )

  def run_migration(self, name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      ["/usr/bin/python3", "-I", str(ROOT / "migrations" / name)],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
    )

  def test_layout_rules_convert_and_preserve_symlink_targets(self) -> None:
    layouts = self.home / ".local/state/arch/workspace-layouts"
    layouts.mkdir(parents=True)
    target = self.scratch / "linked.lua"
    target.write_text('hl.workspace_rule({ workspace = "4", layout = "dwindle" })\n', encoding="utf-8")
    (layouts / "4.lua").symlink_to(target)
    (layouts / "2.lua").write_text('hl.workspace_rule({ workspace = "2", layout = "scrolling" })\n', encoding="utf-8")

    for _ in range(2):
      result = self.run_migration("1791698594.py")
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(result.stdout, "migration.saveWorkspaceLayoutsAsModes\n")

    self.assertEqual((layouts / "2.lua").read_text(encoding="utf-8"), 'o.workspace_mode({ workspace = "2", mode = "scrolling" })\n')
    self.assertTrue((layouts / "4.lua").is_symlink())
    self.assertEqual(target.read_text(encoding="utf-8"), 'o.workspace_mode({ workspace = "4", mode = "dwindle" })\n')

  def test_floating_modes_are_removed_from_home_and_xdg_state_idempotently(self) -> None:
    home_layouts = self.home / ".local/state/arch/workspace-layouts"
    xdg_layouts = self.xdg_state / "arch/workspace-layouts"
    home_layouts.mkdir(parents=True)
    xdg_layouts.mkdir(parents=True)
    (home_layouts / "3.lua").write_text('o.workspace_mode({ workspace = "3", mode = "floating" })\n', encoding="utf-8")
    (home_layouts / "default.lua").write_text('o.workspace_mode({ default = "floating" })\n', encoding="utf-8")
    (xdg_layouts / "5.lua").write_text('o.workspace_mode({ workspace = "5", mode = "floating" })\n', encoding="utf-8")

    for _ in range(2):
      result = self.run_migration("1792937762.py")
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(result.stdout, "migration.removeSavedFloatingWorkspaces\n")

    self.assertEqual((home_layouts / "3.lua").read_text(encoding="utf-8"), 'o.workspace_mode({ workspace = "3", mode = "dwindle" })\n')
    self.assertEqual((home_layouts / "default.lua").read_text(encoding="utf-8"), 'o.workspace_mode({ default = "dwindle" })\n')
    self.assertEqual((xdg_layouts / "5.lua").read_text(encoding="utf-8"), 'o.workspace_mode({ workspace = "5", mode = "dwindle" })\n')


if __name__ == "__main__":
  unittest.main()
