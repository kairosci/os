"""Check converted migrations keep their completion markers and configured values."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from base_test import ROOT, test_environment

sys.path.insert(0, str(ROOT / "src/python"))
from cli.migrate import load_config, pending_migrations


class MigrationMarkerCompatTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="migration-marker-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.home = self.scratch / "home"
    self.home.mkdir()
    self.state = self.scratch / "migration-state"
    self.state.mkdir()
    self.environment = test_environment(
      ARCH_MIGRATION_STATE=self.state,
      HOME=self.home,
      PATH=f"{self.scratch / 'bin'}:{ROOT / 'src/cli'}:{os.environ.get('PATH', '')}",
    )

  def test_python_conversion_uses_old_shell_marker_and_yaml_values(self) -> None:
    migration = ROOT / "migrations/1778623107.py"
    (self.state / "1778623107.sh").touch()
    with patch.dict(os.environ, self.environment):
      config = load_config()
      self.assertEqual(pending_migrations(config, [migration], self.state, self.home), [])

    bin_dir = self.scratch / "bin"
    bin_dir.mkdir()
    package_log = self.scratch / "packages"
    i18n_log = self.scratch / "i18n"
    self._write_stub(
      bin_dir / "arch-i18n",
      "from pathlib import Path\n"
      "import os, sys\n"
      "Path(os.environ['I18N_LOG']).write_text(' '.join(sys.argv[1:]) + '\\n', encoding='utf-8')\n"
      "print('Install MPRIS support for mpv')\n",
    )
    self._write_stub(
      bin_dir / "arch-pkg-add",
      "from pathlib import Path\n"
      "import os, sys\n"
      "Path(os.environ['PACKAGE_LOG']).write_text(' '.join(sys.argv[1:]) + '\\n', encoding='utf-8')\n",
    )
    environment = self.environment | {
      "I18N_LOG": str(i18n_log),
      "PACKAGE_LOG": str(package_log),
    }
    result = subprocess.run(
      ["/usr/bin/python3", "-I", str(migration)],
      check=False,
      capture_output=True,
      text=True,
      env=environment,
    )
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "Install MPRIS support for mpv\n")
    self.assertEqual(i18n_log.read_text(encoding="utf-8"), "migration.installMpvMpris\n")
    self.assertEqual(package_log.read_text(encoding="utf-8"), "mpv-mpris\n")

  def _write_stub(self, path: Path, source: str) -> None:
    path.write_text(f"#!/usr/bin/python3 -I\n{source}", encoding="utf-8")
    path.chmod(0o700)


if __name__ == "__main__":
  unittest.main()
