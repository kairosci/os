"""Check that Python runtime catalogs and tool settings load from data."""

import subprocess
import sys

from base_test import ROOT, test_environment


result = subprocess.run(
  [sys.executable, str(ROOT / "tests/shell.d/python-data-checks.py")],
  env=test_environment(),
  check=False,
)
raise SystemExit(result.returncode)
