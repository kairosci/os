"""Exercise SSH connection reuse through the Python shell test runner."""

import shutil
import subprocess
import sys

from base_test import ROOT, fail_check, test_environment


if not shutil.which("sshd"):
  print("ok - no SSH server; skipping real theme sync connection reuse # SKIP")
  raise SystemExit(0)

for command in ("ssh", "ssh-keygen"):
  if not shutil.which(command):
    fail_check(f"required command is available: {command}")

result = subprocess.run(
  [sys.executable, str(ROOT / "tests/shell.d/fixtures/theme-set-herdr-ssh-reuse.py")],
  env=test_environment(),
  check=False,
)
raise SystemExit(result.returncode)
