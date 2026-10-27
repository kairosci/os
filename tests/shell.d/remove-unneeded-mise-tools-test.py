"""Remove the obsolete Hey and Basecamp tools without deleting user files."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from base_test import ROOT, test_environment


MIGRATION = ROOT / "migrations/1793140400.py"
CONFIG = ROOT / "data/migrations/1793140400.yml"


class RemoveUnneededMiseToolsTest(unittest.TestCase):
  def setUp(self) -> None:
    self.temporary = tempfile.TemporaryDirectory(prefix="remove-mise-tools-")
    self.addCleanup(self.temporary.cleanup)
    self.scratch = Path(self.temporary.name)
    self.home = self.scratch / "home"
    self.bin_dir = self.scratch / "bin"
    self.wrapper_dir = self.home / ".local/bin"
    self.wrapper_dir.mkdir(parents=True)
    self.bin_dir.mkdir()
    self.log = self.scratch / "mise.jsonl"
    mise = self.bin_dir / "mise"
    mise.write_text(
      "#!/usr/bin/python3 -I\n"
      "import json, os, sys\n"
      "with open(os.environ['TEST_MISE_LOG'], 'a', encoding='utf-8') as f:\n"
      "  f.write(json.dumps(sys.argv[1:]) + '\\n')\n",
      encoding="utf-8",
    )
    mise.chmod(0o755)
    self.environment = test_environment(
      HOME=self.home,
      TEST_MISE_LOG=self.log,
      PATH=f"{self.bin_dir}:{os.environ.get('PATH', '')}",
    )

  def run_migration(self) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
      [sys.executable, "-I", str(MIGRATION)],
      check=False,
      capture_output=True,
      text=True,
      env=self.environment,
    )

  def test_removes_only_managed_wrappers_and_unuses_tools(self) -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    template = config["wrappers"]["template"]
    (self.wrapper_dir / "basecamp").write_text(template.format(**config["tools"][1]), encoding="utf-8")
    custom = self.wrapper_dir / "hey"
    custom.write_text(template.format(**config["tools"][0]), encoding="utf-8")
    custom.write_text(custom.read_text(encoding="utf-8").replace("MISE_MINIMUM_RELEASE_AGE=0", "MISE_MINIMUM_RELEASE_AGE=1"), encoding="utf-8")

    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse((self.wrapper_dir / "basecamp").exists())
    self.assertTrue(custom.exists())
    self.assertEqual(
      [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()],
      [
        ["unuse", "--global", "--yes", "github:basecamp/hey-cli"],
        ["unuse", "--global", "--yes", "github:basecamp/basecamp-cli"],
        ["reshim"],
      ],
    )
    self.assertEqual(self.run_migration().returncode, 0)
    self.assertTrue(custom.exists())
    self.assertFalse((self.wrapper_dir / "basecamp").exists())

  def test_keeps_symlinked_wrapper(self) -> None:
    outside = self.scratch / "custom-hey"
    outside.write_text("user-owned wrapper", encoding="utf-8")
    (self.wrapper_dir / "hey").symlink_to(outside)
    result = self.run_migration()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(outside.read_text(encoding="utf-8"), "user-owned wrapper")
    self.assertTrue((self.wrapper_dir / "hey").is_symlink())


if __name__ == "__main__":
  unittest.main()
