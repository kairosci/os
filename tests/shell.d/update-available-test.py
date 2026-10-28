"""Report updates for every package from the configured Arch repositories."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


COMMAND = ROOT / "src/arch/commands/arch-update-available"


class UpdateAvailableTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="update-available-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    self.write_command(
      "checkupdates",
      """#!/bin/bash
case ${TEST_CHECKUPDATES:-updates} in
  updates) printf 'linux 6.1-1 -> 6.1-2\\narch-settings 4.0.0-1 -> 4.0.1-1\\n' ;;
  none) exit 2 ;;
  fail) echo 'check failed' >&2; exit 1 ;;
esac
""",
    )
    self.write_command(
      "arch-i18n",
      """#!/bin/bash
if [[ $1 == --count ]]; then
  printf 'arch-dev-checkout %s new commits on %s\\n' "$4" "$5"
else
  printf 'Il sistema è aggiornato\\n'
fi
""",
    )
    self.write_command(
      "git",
      """#!/bin/bash
shift 2
case $1 in
  rev-parse) printf 'origin/quattro\\n' ;;
  fetch) exit 0 ;;
  rev-list) printf '%s\\n' "${TEST_GIT_BEHIND:-0}" ;;
esac
""",
    )

  def write_command(self, name: str, contents: str) -> None:
    path = self.bin_dir / name
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)

  def run_command(self, **updates: str) -> subprocess.CompletedProcess[str]:
    ap = updates.pop("ARCH_PATH", str(ROOT))
    environment = test_environment(
      ARCH_PATH=ap,
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
      **updates,
    )
    return subprocess.run([str(COMMAND)], env=environment, check=False, capture_output=True, text=True)

  def test_reports_all_package_updates(self) -> None:
    result = self.run_command()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout.splitlines(), [
      "linux 6.1-1 -> 6.1-2",
      "arch-settings 4.0.0-1 -> 4.0.1-1",
    ])

  def test_reports_no_updates_with_localized_message(self) -> None:
    result = self.run_command(TEST_CHECKUPDATES="none")
    self.assertEqual(result.returncode, 1, result.stderr)
    self.assertEqual(result.stdout, "Il sistema è aggiornato\n")

  def test_reports_development_checkout_commits(self) -> None:
    checkout = self.scratch / "checkout"
    checkout.mkdir()
    (checkout / "src").symlink_to(ROOT / "src", target_is_directory=True)
    (checkout / "data").symlink_to(ROOT / "data", target_is_directory=True)
    result = self.run_command(ARCH_PATH=str(checkout), TEST_CHECKUPDATES="none", TEST_GIT_BEHIND="2")
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn("arch-dev-checkout 2 new commits on origin/quattro", result.stdout)


if __name__ == "__main__":
  unittest.main()
