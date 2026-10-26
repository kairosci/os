"""Run the input acceptance helper checks through the Python test runner."""

import subprocess
import sys

from base_test import ROOT, test_environment


result = subprocess.run(
  [sys.executable, str(ROOT / "tests/shell.d/input-acceptance-checks.py")],
  env=test_environment(),
  check=False,
)
raise SystemExit(result.returncode)
