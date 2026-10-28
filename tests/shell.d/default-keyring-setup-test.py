from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
  "default_keyring_setup", ROOT / "src/arch/python/installer_user/setup/default_keyring.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class DefaultKeyringSetupTest(unittest.TestCase):
  def test_creation_is_private_atomic_and_idempotent(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      home = Path(temporary)
      with patch.dict(os.environ, {"ARCH_PATH": str(ROOT), "HOME": str(home), "LANG": "en_US.UTF-8"}):
        self.assertEqual(setup.main(), 0)
        keyrings = home / ".local/share/keyrings"
        keyring = keyrings / "Default_keyring.keyring"
        default = keyrings / "default"
        keyring_content = keyring.read_text(encoding="utf-8")
        self.assertIn("display-name=Default keyring\n", keyring_content)
        self.assertRegex(keyring_content, r"ctime=\d+\n")
        self.assertEqual(default.read_text(encoding="utf-8"), "Default_keyring\n")
        self.assertEqual(keyrings.stat().st_mode & 0o777, 0o700)
        self.assertEqual(keyring.stat().st_mode & 0o777, 0o600)
        self.assertEqual(default.stat().st_mode & 0o777, 0o644)
        self.assertEqual(list(keyrings.glob(".*.tmp")), [])

        keyring.write_text("preserve existing keyring\n", encoding="utf-8")
        keyring.chmod(0o644)
        default.write_text("custom default\n", encoding="utf-8")
        default.chmod(0o600)
        self.assertEqual(setup.main(), 0)
        self.assertEqual(keyring.read_text(encoding="utf-8"), "preserve existing keyring\n")
        self.assertEqual(default.read_text(encoding="utf-8"), "custom default\n")
        self.assertEqual(keyring.stat().st_mode & 0o777, 0o600)
        self.assertEqual(default.stat().st_mode & 0o777, 0o644)

  def test_symlinked_keyring_is_refused_without_touching_its_target(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      home = Path(temporary)
      keyrings = home / ".local/share/keyrings"
      keyrings.mkdir(parents=True)
      target = home / "outside"
      target.write_text("keep secret\n", encoding="utf-8")
      (keyrings / "Default_keyring.keyring").symlink_to(target)
      with patch.dict(os.environ, {"ARCH_PATH": str(ROOT), "HOME": str(home), "LANG": "it_IT.UTF-8"}), contextlib.redirect_stderr(io.StringIO()) as error:
        self.assertEqual(setup.main(), 1)
      self.assertEqual(
        error.getvalue(),
        "Impossibile configurare in sicurezza il portachiavi predefinito.\n",
      )
      self.assertTrue((keyrings / "Default_keyring.keyring").is_symlink())
      self.assertEqual(target.read_text(encoding="utf-8"), "keep secret\n")


if __name__ == "__main__":
  unittest.main()
