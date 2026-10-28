"""Check that session markers are stable across shell restarts."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


MARKER_COMMAND = ROOT / "src/arch/commands/arch-background-session-mark"


class BackgroundSessionMarkerTest(unittest.TestCase):
  def test_invalid_settings_fail_with_a_message_without_a_traceback(self) -> None:
    with tempfile.TemporaryDirectory(prefix="background-session-invalid-settings-") as temporary:
      scratch = Path(temporary)
      arch = scratch / "arch"
      (arch / "data/cli").mkdir(parents=True)
      (arch / "src").symlink_to(ROOT / "src", target_is_directory=True)
      (arch / "data/cli/background-session-mark.yml").write_text("[]\n", encoding="utf-8")
      environment = test_environment(AP=arch, HOME=scratch / "home")

      result = subprocess.run(
        [str(MARKER_COMMAND)], env=environment, check=False, capture_output=True, text=True
      )

      self.assertEqual(result.returncode, 1)
      self.assertIn("Could not load background session marker configuration", result.stderr)
      self.assertNotIn("Traceback", result.stderr)

  def test_marker_is_idempotent_for_the_same_session(self) -> None:
    with tempfile.TemporaryDirectory(prefix="background-session-") as temporary:
      scratch = Path(temporary)
      home = scratch / "home"
      state = scratch / "state"
      home.mkdir()
      environment = test_environment(
        HOME=home,
        XDG_STATE_HOME=state,
        ARCH_SESSION_ID="login-one",
      )

      first = subprocess.run([str(MARKER_COMMAND)], env=environment, check=False)
      self.assertEqual(first.returncode, 0)
      marker = state / "arch/background-intro.session-id"
      self.assertEqual(marker.read_text(encoding="utf-8"), "login-one\n")
      marker.touch()
      os.utime(marker, ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))
      original_mtime = marker.stat().st_mtime_ns

      repeated = subprocess.run([str(MARKER_COMMAND)], env=environment, check=False)
      self.assertEqual(repeated.returncode, 0)
      self.assertEqual(marker.stat().st_mtime_ns, original_mtime)

      environment["ARCH_SESSION_ID"] = "login-two"
      next_session = subprocess.run([str(MARKER_COMMAND)], env=environment, check=False)
      self.assertEqual(next_session.returncode, 0)
      self.assertEqual(marker.read_text(encoding="utf-8"), "login-two\n")


if __name__ == "__main__":
  unittest.main()
