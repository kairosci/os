"""Check that menu row text does not shift with the selected border."""

from __future__ import annotations

import re

from base_test import ROOT, fail_check, pass_check


menu_qml = (ROOT / "src/shell/plugins/menu/Menu.qml").read_text(encoding="utf-8")
if not re.search(r"rowReservedBorderLeft:\s*Border\.left\(selectedBorderSpec\)", menu_qml) or not re.search(
  r"rowReservedBorderRight:\s*Border\.right\(selectedBorderSpec\)", menu_qml
):
  fail_check("Menu rows reserve selected border insets")
pass_check("Menu rows reserve selected border insets")

if re.search(r"anchors\.(left|right)Margin:[^\n]*\brow\.border(Left|Right)\b", menu_qml):
  fail_check("Menu row content does not depend on current selected border state")
pass_check("Menu row content does not depend on current selected border state")
