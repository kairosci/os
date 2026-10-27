"""Keep Bash microsecond clocks numeric under comma-decimal locales."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from base_test import ROOT, test_environment


COMMANDS = (
  "arch-dev-benchmark-cli",
  "arch-dev-benchmark-theme-switcher",
)


class EpochRealtimeLocaleTest(unittest.TestCase):
  def test_microsecond_clock_ignores_locale_decimal_separator(self) -> None:
    with tempfile.TemporaryDirectory(prefix="epochrealtime-locale-") as directory:
      locale_root = Path(directory) / "locales"
      locale_root.mkdir()
      generated = subprocess.run(
        ["localedef", "-i", "da_DK", "-f", "UTF-8", str(locale_root / "da_DK.UTF-8")],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
      )
      if generated.returncode != 0:
        self.skipTest("localedef cannot build da_DK")

      environment = test_environment(
        LOCPATH=locale_root,
        LC_ALL="da_DK.UTF-8",
        PATH=os.environ.get("PATH", ""),
      )
      clock = subprocess.run(
        ["bash", "-c", 'printf "%s" "$EPOCHREALTIME"'],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
      )
      self.assertEqual(clock.returncode, 0, clock.stderr)
      self.assertIn(",", clock.stdout)

      extraction = (
        'source <(awk "/^now_us\\(\\) \\{/ { copying=1 } copying { print } copying && /^}\\$/ { exit }" "$1")\n'
        "now_us\n"
      )
      for name in COMMANDS:
        with self.subTest(command=name):
          result = subprocess.run(
            ["bash", "-c", extraction, "_", str(ROOT / "src/cli" / name)],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
          )
          self.assertEqual(result.returncode, 0, result.stderr)
          self.assertRegex(result.stdout.strip(), r"^[0-9]{16}$")


if __name__ == "__main__":
  unittest.main()
