"""Migrate the Cloudflare CLI installer while respecting the opt-out marker."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1789310715.py"


class CloudflareCliMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="cloudflare-cli-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.home = Path(self.temporary.name)
    self.bin_dir = self.home / "bin"
    self.bin_dir.mkdir()
    self.log = self.home / "calls"
    self.write_command("arch-i18n", 'printf "localized:%s\\n" "$1" >>"$TEST_LOG"\n')
    self.write_command("arch-mise-install", 'printf "install:%s\\n" "$*" >>"$TEST_LOG"\n')

  def write_command(self, name: str, body: str) -> None:
    command = self.bin_dir / name
    command.write_text(f"#!/bin/bash\nset -euo pipefail\n{body}", encoding="utf-8")
    command.chmod(0o755)

  def run_migration(self) -> subprocess.CompletedProcess[str]:
    environment = test_environment(
      ARCH_PATH=str(ROOT),
      HOME=str(self.home),
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
      TEST_LOG=str(self.log),
    )
    return subprocess.run(
      ["python3", "-I", str(MIGRATION)],
      env=environment,
      check=False,
      capture_output=True,
      text=True,
    )

  def test_installs_when_user_kept_preinstalls(self) -> None:
    result = self.run_migration()

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(
      self.log.read_text(encoding="utf-8").splitlines(),
      ["localized:migration.installCloudflareCli", "install:npm:cf cf"],
    )

  def test_respects_preinstalls_opt_out(self) -> None:
    marker = self.home / ".local/state/arch/preinstalls-removed"
    marker.parent.mkdir(parents=True)
    marker.touch()

    result = self.run_migration()

    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(
      self.log.read_text(encoding="utf-8").splitlines(),
      ["localized:migration.installCloudflareCli"],
    )


if __name__ == "__main__":
  unittest.main()
