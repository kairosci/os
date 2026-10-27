"""Check hardware decoding defaults and configuration precedence in mpv."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check


if shutil.which("mpv") is None:
  print("ok - mpv is not installed, so the shipped system config cannot be loaded # SKIP")
  raise SystemExit(0)


def configured_hwdec(*options: str) -> str:
  result = subprocess.run(
    [
      "mpv",
      "--no-config",
      *options,
      "--vo=null",
      "--ao=null",
      "--frames=1",
      "--term-status-msg=",
      "--term-playing-msg=" + "hwdec=" + "$" + "{hwdec}",
      "av://lavfi:testsrc",
    ],
    capture_output=True,
    text=True,
    env=os.environ.copy(),
    check=False,
  )
  if result.returncode != 0:
    fail_check(f"mpv loads the config and plays a test source: {result.stdout}{result.stderr}")
  match = re.search(r"^hwdec=(.*)$", result.stdout + result.stderr, re.MULTILINE)
  if not match:
    fail_check(f"mpv reports its hardware decoder option: {result.stdout}{result.stderr}")
  return match.group(1)


stock = configured_hwdec()
if stock != "no":
  fail_check(f"mpv's own default is software decoding: got {stock}")

system_config = ROOT / "etc/mpv/mpv.conf"
shipped = configured_hwdec(f"--include={system_config}")
if shipped != "auto-safe":
  fail_check(f"the shipped system config turns on safe hardware decoding: got {shipped}")
pass_check("the shipped system config turns on safe hardware decoding")

with tempfile.TemporaryDirectory(prefix="mpv-config-") as temporary:
  user_config = Path(temporary) / "user.conf"
  user_config.write_text("hwdec=no\n", encoding="utf-8")
  layered = configured_hwdec(f"--include={system_config}", f"--include={user_config}")
if layered != "no":
  fail_check(f"a user config read after the system config keeps its hwdec: got {layered}")
pass_check("a user config read after the system config keeps its hwdec")
