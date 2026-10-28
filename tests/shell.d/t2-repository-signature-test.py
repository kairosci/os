"""Verify the T2 package repository rejects unsigned package payloads."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


REPOSITORY_SETUP = ROOT / "src/arch/python/installer/hardware/pacman_repositories.py"


class T2RepositorySignatureTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="t2-repository-signature-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.config = self.scratch / "pacman.conf"
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    self._write_stub(
      "lspci",
      "import sys\n"
      "print('00:00.0 Apple Inc. T2 [106b:1801]')\n",
    )
    self._write_stub(
      "arch-i18n",
      "import sys\n"
      "print(sys.argv[1])\n",
    )
    self._write_stub(
      "sudo",
      "import os, sys\n"
      "os.execv('/usr/bin/' + sys.argv[1], ['/usr/bin/' + sys.argv[1], *sys.argv[2:]])\n",
    )
    self.environment = test_environment(
      ARCH_PACMAN_CONFIG_PATH=self.config,
      PATH=f"{self.bin_dir}:{ROOT / 'src/arch/commands'}:{os.environ.get('PATH', '')}",
    )

  def test_new_config_requires_package_signatures(self) -> None:
    self.config.write_text("[options]\nSigLevel = Required DatabaseOptional\n", encoding="utf-8")
    setup = subprocess.run(
      ["/usr/bin/python3", "-I", str(REPOSITORY_SETUP)],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
    )
    self.assertEqual(setup.returncode, 0, setup.stderr)
    self.assertIn("SigLevel = PackageRequired", self.config.read_text(encoding="utf-8"))

  def _write_stub(self, name: str, source: str) -> None:
    path = self.bin_dir / name
    path.write_text(f"#!/usr/bin/python3 -I\n{source}", encoding="utf-8")
    path.chmod(0o700)


if __name__ == "__main__":
  unittest.main()
