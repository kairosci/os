"""Install the stock initramfs hook defaults before rebuilding images."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1792869000.py"
SOURCES = (
  "00-arch-hooks.conf",
  "arch_hooks.conf",
)


class InitramfsHooksMigrationTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="initramfs-hooks-migration-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    self.config_dir = self.scratch / "mkinitcpio.conf.d"
    self.config_dir.mkdir()
    self.rebuild_log = self.scratch / "rebuild.log"

    i18n = self.bin_dir / "arch-i18n"
    i18n.write_text("#!/usr/bin/python3 -I\nimport sys\nprint(sys.argv[1])\n", encoding="utf-8")
    i18n.chmod(0o755)
    sudo = self.bin_dir / "sudo"
    sudo.write_text(
      "#!/usr/bin/python3 -I\n"
      "import os, sys\n"
      "if sys.argv[1] == 'install' and os.environ.get('ARCH_TEST_INSTALL_STATUS'):\n"
      "  raise SystemExit(int(os.environ['ARCH_TEST_INSTALL_STATUS']))\n"
      "os.execvpe(sys.argv[1], sys.argv[1:], os.environ)\n",
      encoding="utf-8",
    )
    sudo.chmod(0o755)
    mkinitcpio = self.bin_dir / "mkinitcpio"
    mkinitcpio.write_text(
      "#!/usr/bin/python3 -I\n"
      "import os, pathlib, sys\n"
      f"pathlib.Path({str(self.rebuild_log)!r}).write_text(' '.join(sys.argv[1:]) + '\\n', encoding='utf-8')\n"
      "raise SystemExit(int(os.environ.get('ARCH_TEST_REBUILD_STATUS', '0')))\n",
      encoding="utf-8",
    )
    mkinitcpio.chmod(0o755)
    self.environment = test_environment(
      ARCH_MKINITCPIO_CONFIG_DIR=self.config_dir,
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

  def test_installs_configs_then_rebuilds_images(self) -> None:
    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.useArchInitramfsHooks\n")
    for name in SOURCES:
      installed = self.config_dir / name
      self.assertEqual(installed.read_bytes(), (ROOT / "etc/mkinitcpio.conf.d" / name).read_bytes())
      self.assertEqual(installed.stat().st_mode & 0o777, 0o644)
    self.assertEqual(self.rebuild_log.read_text(encoding="utf-8"), "-P\n")

  def test_install_failure_stops_before_rebuilding(self) -> None:
    self.environment["ARCH_TEST_INSTALL_STATUS"] = "23"
    result = self.run_migration()
    self.assertEqual(result.returncode, 23)
    self.assertFalse(self.rebuild_log.exists())

  def test_rebuild_failure_keeps_migration_pending(self) -> None:
    self.environment["ARCH_TEST_REBUILD_STATUS"] = "37"
    result = self.run_migration()
    self.assertEqual(result.returncode, 37)
    for name in SOURCES:
      self.assertTrue((self.config_dir / name).is_file())


if __name__ == "__main__":
  unittest.main()
