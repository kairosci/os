"""Check that the Windows VM does not restart automatically."""

from __future__ import annotations

import re

from base_test import ROOT, fail_check, pass_check


command = (ROOT / "src/commands/arch-windows-vm").read_text(encoding="utf-8")
if not re.search(r'^    restart: "no"$', command, re.MULTILINE):
  fail_check("Windows VM uses manual startup by default")
pass_check("Windows VM uses manual startup by default")

if re.search(r"^    restart: unless-stopped$", command, re.MULTILINE):
  fail_check("Windows VM does not restart automatically at boot")
pass_check("Windows VM does not restart automatically at boot")

if not re.search(r'title:"?Windows VM - os"', command):
  fail_check("Windows VM launches FreeRDP with its expected title")
pass_check("Windows VM launches FreeRDP with its expected title")
