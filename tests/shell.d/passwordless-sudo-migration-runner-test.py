"""Run the passwordless-sudo cleanup only when its machine marker is absent."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1788163635.py"


class PasswordlessSudoMigrationRunnerTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="passwordless-sudo-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.root = self.scratch / "arch"
    (self.root / "data/migrations").mkdir(parents=True)
    helper = self.root / "src/cli/arch-sudo-passwordless"
    helper.parent.mkdir(parents=True)
    helper.write_text(
      "#!/usr/bin/python3 -I\n"
      "import os, pathlib, sys\n"
      "pathlib.Path(os.environ['ARCH_TEST_HELPER_LOG']).open('a').write(' '.join(sys.argv[1:]) + '\\n')\n"
      "status_name = 'ARCH_TEST_HELPER_STATUS' if sys.argv[1] == '__migration-complete' else 'ARCH_TEST_MIGRATE_STATUS'\n"
      "raise SystemExit(int(os.environ.get(status_name, '0')))\n",
      encoding="utf-8",
    )
    helper.chmod(0o755)
    migration_data = self.root / "data/migrations/1788163635.yml"
    migration_data.write_bytes((ROOT / "data/migrations/1788163635.yml").read_bytes())
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    i18n = self.bin_dir / "arch-i18n"
    i18n.write_text("#!/usr/bin/python3 -I\nimport sys\nprint(sys.argv[1])\n", encoding="utf-8")
    i18n.chmod(0o755)
    sudo = self.bin_dir / "sudo"
    sudo.write_text(
      "#!/usr/bin/python3 -I\n"
      "import os, pathlib, sys\n"
      "pathlib.Path(os.environ['ARCH_TEST_SUDO_LOG']).write_text(' '.join(sys.argv[1:]) + '\\n')\n"
      "os.execvpe(sys.argv[1], sys.argv[1:], os.environ)\n",
      encoding="utf-8",
    )
    sudo.chmod(0o755)
    self.helper_log = self.scratch / "helper.log"
    self.sudo_log = self.scratch / "sudo.log"
    self.environment = test_environment(
      ARCH_PATH=self.root,
      ARCH_TEST_HELPER_LOG=self.helper_log,
      ARCH_TEST_SUDO_LOG=self.sudo_log,
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

  def test_complete_machine_migration_does_not_elevate(self) -> None:
    self.environment["ARCH_TEST_HELPER_STATUS"] = "0"
    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.removeLegacyPasswordlessSudoGrants\n")
    self.assertEqual(self.helper_log.read_text(encoding="utf-8"), "__migration-complete\n")
    self.assertFalse(self.sudo_log.exists())

  def test_incomplete_machine_migration_elevates_and_propagates_failure(self) -> None:
    self.environment["ARCH_TEST_HELPER_STATUS"] = "1"
    self.environment["ARCH_TEST_MIGRATE_STATUS"] = "23"
    result = self.run_migration()
    self.assertEqual(result.returncode, 23, result.stderr)
    helper = self.root / "src/cli/arch-sudo-passwordless"
    self.assertEqual(self.sudo_log.read_text(encoding="utf-8"), f"{helper} __migrate\n")
    self.assertEqual(self.helper_log.read_text(encoding="utf-8"), "__migration-complete\n__migrate\n")


if __name__ == "__main__":
  unittest.main()
