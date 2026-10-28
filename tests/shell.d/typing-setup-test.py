"""Check setup language selection and its menu model."""

from __future__ import annotations

import subprocess
import sys

from base_test import ROOT, fail_check, pass_check, test_environment


checks = subprocess.run(
  [sys.executable, str(ROOT / "tests/shell.d/typing-setup-checks.py")],
  capture_output=True,
  text=True,
  env=test_environment(),
  check=False,
)
if checks.returncode != 0:
  fail_check(f"typing setup checks: {checks.stdout}{checks.stderr}")
pass_check("typing setup checks")

model_check = r"""
const assert = require("node:assert/strict")
const menu = require(process.cwd() + "/src/arch/shell/plugins/menu/MenuModel.js")
const options = ["French", "\tJapanese (Mozc)", "x\tSame label\tfirst", "x\tSame label\tsecond"]
assert.equal(menu.dmenuValue(options[2]), "Same label\tfirst")
assert.deepEqual(menu.dmenuSelections(options, ["Same label\tsecond", "French", "stale"]), ["French", "Same label\tsecond"])
assert.deepEqual(menu.dmenuSelections(options, ["Same label\tsecond", "French", "stale"], true), ["Same label\tsecond", "French"])
assert.deepEqual(menu.toggleDmenuSelection(["French"], "French"), [])
assert.deepEqual(menu.toggleDmenuSelection(["French"], "Japanese (Mozc)"), ["French", "Japanese (Mozc)"])
"""
result = subprocess.run(
  ["node", "-e", model_check],
  capture_output=True,
  text=True,
  cwd=ROOT,
  env=test_environment(),
  check=False,
)
if result.returncode != 0:
  fail_check(f"typing setup menu model: {result.stdout}{result.stderr}")
pass_check("typing setup menu model preserves stable selection values")
