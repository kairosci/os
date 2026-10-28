"""Check that detached shell commands use a login shell."""

from __future__ import annotations

import re

from base_test import ROOT, fail_check, pass_check


util_qml = (ROOT / "src/arch/shell/Commons/Util.qml").read_text(encoding="utf-8")
if not re.search(r'function execDetached\(command\)[\s\S]*Quickshell\.execDetached\(\["bash", "-lc", command\]\)', util_qml):
  fail_check("detached command helper uses a login shell")
pass_check("detached command helper uses a login shell")
