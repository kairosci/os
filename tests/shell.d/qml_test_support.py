"""Run one Qt 6 QML test directory and report its TAP result."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

from base_test import ROOT, fail_check, pass_check


def run_qml_test(directory: str, description: str) -> None:
  candidates = (
    Path("/usr/lib/qt6/bin/qmltestrunner"),
    Path("/usr/lib/qt6/qmltestrunner"),
  )
  runner = next((candidate for candidate in candidates if candidate.is_file() and os.access(candidate, os.X_OK)), None)
  if runner is None:
    print(f"ok - qt6 qmltestrunner not found; skipping {description} # SKIP")
    return

  environment = os.environ.copy()
  environment.update({"QT_QPA_PLATFORM": "offscreen", "QT_QUICK_BACKEND": "software"})
  result = subprocess.run(
    [str(runner), "-input", str(ROOT / "tests/shell.d" / directory / "qml"), "-o", "-,txt"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=environment,
    check=False,
  )
  if result.returncode != 0:
    fail_check(f"{description}: {result.stdout}")
  pass_check(description)
