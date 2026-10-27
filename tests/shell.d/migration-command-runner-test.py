"""Verify command migrations preserve order and optional failures."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


IGNORED_FAILURE_MIGRATION = ROOT / "migrations/1791640449.py"
ORDERED_MIGRATION = ROOT / "migrations/1792020559.py"
BRAVE_MIGRATION = ROOT / "migrations/1788595060.py"
USAGE_WIDGET_MIGRATION = ROOT / "migrations/1793067182.py"
WORKSPACE_TOOL_MIGRATION = ROOT / "migrations/1793104430.py"


class MigrationCommandRunnerTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="migration-command-runner-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    self.call_log = self.scratch / "calls.jsonl"
    self.home = self.scratch / "home"
    self.home.mkdir()
    stub = self.bin_dir / "command"
    stub.write_text(
      "#!/usr/bin/python3 -I\n"
      "import json, os, pathlib, sys\n"
      "name = pathlib.Path(sys.argv[0]).name\n"
      "with open(os.environ['CALL_LOG'], 'a', encoding='utf-8') as stream:\n"
      "  stream.write(json.dumps([name, *sys.argv[1:]]) + '\\n')\n"
      "if name == 'arch-i18n': print(sys.argv[1])\n"
      "if name == 'mise' and sys.argv[1:3] == ['ls', 'herdr']: print('herdr latest')\n"
      "if os.environ.get('FAIL_COMMAND') == name: raise SystemExit(9)\n",
      encoding="utf-8",
    )
    stub.chmod(0o755)
    names = (
      "arch-i18n",
      "arch-bar",
      "arch-theme-set-fcitx5",
      "arch-theme-refresh",
      "arch-install-chromium-copy-url",
      "arch-install-chromium-ytdlp",
      "arch-pkg-drop",
      "mise",
    )
    for name in names:
      (self.bin_dir / name).symlink_to(stub)
    self.environment = test_environment(
      HOME=self.home,
      CALL_LOG=self.call_log,
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
    )

  def run_migration(self, path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      ["/usr/bin/python3", "-I", str(path)],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
    )

  def calls(self) -> list[list[str]]:
    return [json.loads(line) for line in self.call_log.read_text(encoding="utf-8").splitlines()]

  def test_optional_bar_move_failure_is_ignored(self) -> None:
    self.environment["FAIL_COMMAND"] = "arch-bar"
    result = self.run_migration(IGNORED_FAILURE_MIGRATION)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.moveKeyboardLayoutWidget\n")
    self.assertEqual(
      self.calls(),
      [
        ["arch-i18n", "migration.moveKeyboardLayoutWidget"],
        ["arch-bar", "move", "arch.keyboard-layout", "--from-section", "center", "--section", "right", "--index", "0"],
      ],
    )

  def test_required_commands_run_in_order_and_stop_on_failure(self) -> None:
    result = self.run_migration(ORDERED_MIGRATION)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.themeFcitxCandidateWindow\n")
    self.assertEqual(
      self.calls(),
      [
        ["arch-i18n", "migration.themeFcitxCandidateWindow"],
        ["arch-theme-set-fcitx5", "--activate"],
        ["arch-theme-refresh"],
      ],
    )

  def test_brave_origin_extension_hosts_are_registered_in_order(self) -> None:
    result = self.run_migration(BRAVE_MIGRATION)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.registerBraveOriginExtensionHosts\n")
    self.assertEqual(
      self.calls(),
      [
        ["arch-i18n", "migration.registerBraveOriginExtensionHosts"],
        ["arch-install-chromium-copy-url"],
        ["arch-install-chromium-ytdlp"],
      ],
    )

    self.call_log.unlink()
    self.environment["FAIL_COMMAND"] = "arch-theme-set-fcitx5"
    failed = self.run_migration(ORDERED_MIGRATION)
    self.assertEqual(failed.returncode, 9)
    self.assertEqual(
      self.calls(),
      [
        ["arch-i18n", "migration.themeFcitxCandidateWindow"],
        ["arch-theme-set-fcitx5", "--activate"],
      ],
    )

  def test_retired_usage_widget_is_removed_without_changing_other_settings(self) -> None:
    config_dir = self.home / ".config/arch"
    config_dir.mkdir(parents=True)
    config = config_dir / "shell.json"
    config.write_text(
      '{"bar":{"layout":{"left":["arch.menu",{"id":"arch.agents"}],'
      '"right":[{"id":"third.widget"}]}},'
      '"disabledPlugins":["arch.agents","third.widget"]}',
      encoding="utf-8",
    )
    config.chmod(0o640)

    result = self.run_migration(USAGE_WIDGET_MIGRATION)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.removeRetiredUsageWidget\n")
    self.assertEqual(
      json.loads(config.read_text(encoding="utf-8")),
      {
        "bar": {"layout": {"left": ["arch.menu"], "right": [{"id": "third.widget"}]}},
        "disabledPlugins": ["third.widget"],
      },
    )
    self.assertEqual(config.stat().st_mode & 0o777, 0o640)
    self.assertEqual(self.calls(), [["arch-i18n", "migration.removeRetiredUsageWidget"]])

  def test_retired_workspace_tool_removes_only_its_files_and_installation(self) -> None:
    for relative in (
      ".local/bin/herdr",
      ".local/share/mise/shims/herdr",
      ".local/state/arch/toggles/herdr-theme-sync",
    ):
      path = self.home / relative
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text("retired", encoding="utf-8")
    installation = self.home / ".local/share/mise/installs/herdr/1.0/bin"
    installation.mkdir(parents=True)
    (installation / "herdr").write_text("retired", encoding="utf-8")
    config = self.home / ".config/herdr/settings.yml"
    config.parent.mkdir(parents=True)
    config.write_text("retired", encoding="utf-8")
    preserved = self.home / ".config/herdr-backup/settings.yml"
    preserved.parent.mkdir(parents=True)
    preserved.write_text("keep", encoding="utf-8")

    result = self.run_migration(WORKSPACE_TOOL_MIGRATION)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.removeRetiredWorkspaceTool\n")
    self.assertFalse((self.home / ".local/bin/herdr").exists())
    self.assertFalse((self.home / ".local/share/mise/installs/herdr").exists())
    self.assertFalse((self.home / ".config/herdr").exists())
    self.assertEqual(preserved.read_text(encoding="utf-8"), "keep")
    self.assertEqual(
      self.calls(),
      [
        ["arch-i18n", "migration.removeRetiredWorkspaceTool"],
        ["arch-pkg-drop", "arch-herdr", "herdr"],
        ["mise", "ls", "herdr"],
        ["mise", "unuse", "-g", "herdr"],
        ["mise", "uninstall", "-a", "herdr"],
      ],
    )

    outside = self.scratch / "outside"
    outside.mkdir()
    protected = outside / "herdr"
    protected.write_text("keep", encoding="utf-8")
    bin_directory = self.home / ".local/bin"
    bin_directory.rmdir()
    bin_directory.symlink_to(outside, target_is_directory=True)
    self.call_log.unlink()

    repeated = self.run_migration(WORKSPACE_TOOL_MIGRATION)
    self.assertEqual(repeated.returncode, 0, repeated.stderr)
    self.assertEqual(protected.read_text(encoding="utf-8"), "keep")

if __name__ == "__main__":
  unittest.main()
