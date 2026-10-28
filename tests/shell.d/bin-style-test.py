"""Check that CLI scripts use command and notification helpers."""

from __future__ import annotations

import re
import subprocess

from base_test import ROOT, fail_check, pass_check, test_environment


cli = ROOT / "src/arch/commands"
environment = test_environment()
command_checks = subprocess.run(
  ["rg", "-l", "command -v", str(cli)],
  capture_output=True,
  text=True,
  env=environment,
  check=False,
).stdout.splitlines()
excluded = re.compile(r"/arch-(?:cmd-|pkg-|upgrade-to-quattro)")
raw_command_checks = [path for path in command_checks if not excluded.search(path)]
if raw_command_checks:
  fail_check("bin commands use command helpers: " + "\n".join(raw_command_checks))
pass_check("bin commands use command helpers")

raw_notifications = subprocess.run(
  ["rg", "-l", "-P", r"^[[:space:]]*[^#[:space:]].*\bnotify-send\b", str(cli)],
  capture_output=True,
  text=True,
  env=environment,
  check=False,
).stdout.splitlines()
if raw_notifications:
  fail_check("bin commands use the notification helper, never notify-send: " + "\n".join(raw_notifications))
pass_check("bin commands use the notification helper")
