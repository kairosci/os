"""Run input-method setup checks through the Python test runner."""

import subprocess
import sys

from base_test import ROOT, test_environment


result = subprocess.run(
  [sys.executable, str(ROOT / "tests/shell.d/input-method-checks.py")],
  env=test_environment(),
  check=False,
)
raise SystemExit(result.returncode)
