"""Verify system lock stops dependent terminals in order."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


COMMAND = ROOT / "src/commands/arch-system-lock"
MOCK_COMMAND = """#!/usr/bin/python3
import os
from pathlib import Path
import sys

with Path(os.environ["CALL_LOG"]).open("a", encoding="utf-8") as log:
  log.write(f"{Path(sys.argv[0]).name} {' '.join(sys.argv[1:])}\\n")
"""
MOCK_PGREP = "#!/usr/bin/python3\nraise SystemExit(1)\n"


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary_directory:
    temporary_path = Path(temporary_directory)
    mock_bin = temporary_path / "bin"
    mock_bin.mkdir()
    call_log = temporary_path / "calls"
    for command in ("arch-shell", "hyprctl", "pkill", "timeout"):
      executable = mock_bin / command
      executable.write_text(MOCK_COMMAND, encoding="utf-8")
      executable.chmod(0o755)
    pgrep = mock_bin / "pgrep"
    pgrep.write_text(MOCK_PGREP, encoding="utf-8")
    pgrep.chmod(0o755)

    environment = test_environment(CALL_LOG=str(call_log))
    environment["PATH"] = f"{mock_bin}:{environment['PATH']}"
    result = subprocess.run(
      [str(COMMAND)],
      check=False,
      env=environment,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
      fail_check("system lock command completes successfully")

    calls = call_log.read_text(encoding="utf-8").splitlines()
    shutdown = [call for call in calls if call.startswith(("pkill ", "timeout "))]
    expected = [
      "pkill -x ttfx",
      "timeout 1s pidwait -x ttfx",
      "pkill -f [o]rg.arch.screensaver",
    ]
    if shutdown != expected:
      fail_check("system lock waits for ttfx before closing its terminal")
    pass_check("system lock waits for ttfx before closing its terminal")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
