"""Verify the tiled fullscreen toggle sends the expected Hyprland dispatch."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


COMMAND = ROOT / "src/arch/commands/arch-hyprland-window-tiled-fullscreen-toggle"
MOCK_HYPRCTL = """#!/usr/bin/python3
import json
import os
from pathlib import Path
import sys

if sys.argv[1:] == ["activewindow", "-j"]:
  print(json.dumps({"fullscreenClient": int(os.environ["HYPR_FULLSCREEN_CLIENT"])}))
elif sys.argv[1] == "dispatch":
  with Path(os.environ["HYPRCTL_LOG"]).open("a", encoding="utf-8") as log:
    log.write(" ".join(sys.argv[1:]) + "\\n")
else:
  raise SystemExit(1)
"""


def run_toggle(mock_bin: Path, log: Path, fullscreen_client: int) -> list[str]:
  environment = test_environment(
    HYPRCTL_LOG=str(log),
    HYPR_FULLSCREEN_CLIENT=str(fullscreen_client),
  )
  environment["PATH"] = f"{mock_bin}:{environment['PATH']}"
  result = subprocess.run(
    [str(COMMAND)],
    check=False,
    env=environment,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  if result.returncode != 0:
    fail_check("tiled fullscreen toggle completes successfully")
  return log.read_text(encoding="utf-8").splitlines()


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary_directory:
    temporary_path = Path(temporary_directory)
    mock_bin = temporary_path / "bin"
    mock_bin.mkdir()
    hyprctl = mock_bin / "hyprctl"
    hyprctl.write_text(MOCK_HYPRCTL, encoding="utf-8")
    hyprctl.chmod(0o755)
    log = temporary_path / "hyprctl.log"

    calls = run_toggle(mock_bin, log, 0)
    if "dispatch hl.dsp.window.fullscreen_state({ internal = 0, client = 2 })" not in calls:
      fail_check("tiled fullscreen enables client fullscreen")
    pass_check("tiled fullscreen enables client fullscreen")

    log.write_text("", encoding="utf-8")
    calls = run_toggle(mock_bin, log, 2)
    if "dispatch hl.dsp.window.fullscreen_state({ internal = 0, client = 0 })" not in calls:
      fail_check("tiled fullscreen disables client fullscreen")
    pass_check("tiled fullscreen disables client fullscreen")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
