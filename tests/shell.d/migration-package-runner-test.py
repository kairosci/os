"""Verify package migrations localize their reason and stop before drops on add failure."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1781286586.py"


class MigrationPackageRunnerTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="migration-package-runner-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.bin_dir = self.scratch / "bin"
    self.bin_dir.mkdir()
    self.log = self.scratch / "calls.jsonl"
    stub = self.bin_dir / "command"
    stub.write_text(
      "#!/usr/bin/python3\n"
      "import json, os, pathlib, sys\n"
      "name = pathlib.Path(sys.argv[0]).name\n"
      "with open(os.environ['CALL_LOG'], 'a', encoding='utf-8') as output:\n"
      "  output.write(json.dumps([name, *sys.argv[1:]]) + '\\n')\n"
      "if name == 'arch-i18n': print(sys.argv[1])\n"
      "if name == 'arch-pkg-add' and os.environ.get('FAIL_ADD') == '1': raise SystemExit(7)\n",
      encoding="utf-8",
    )
    stub.chmod(0o755)
    for name in ("arch-i18n", "arch-pkg-add", "arch-pkg-drop"):
      (self.bin_dir / name).symlink_to(stub)
    self.environment = test_environment(
      CALL_LOG=self.log,
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

  def calls(self) -> list[list[str]]:
    return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

  def test_localizes_then_adds_and_drops_packages(self) -> None:
    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout, "migration.replaceSatty\n")
    self.assertEqual(
      self.calls(),
      [
        ["arch-i18n", "migration.replaceSatty"],
        ["arch-pkg-add", "tensaku"],
        ["arch-pkg-drop", "satty"],
      ],
    )

  def test_failed_add_does_not_remove_the_existing_package(self) -> None:
    self.environment["FAIL_ADD"] = "1"
    result = self.run_migration()
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(
      self.calls(),
      [
        ["arch-i18n", "migration.replaceSatty"],
        ["arch-pkg-add", "tensaku"],
      ],
    )


if __name__ == "__main__":
  unittest.main()
