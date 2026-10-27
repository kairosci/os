"""Check that plugin changes update panel loaders in place."""

from __future__ import annotations

import re

from base_test import ROOT, fail_check, pass_check


shell_qml = (ROOT / "src/shell/shell.qml").read_text(encoding="utf-8")
if not re.search(r"Instantiator \{\s*model: panelEntryModel", shell_qml) or "panelEntries" in shell_qml:
  fail_check("panel loaders come from a model synced in place, not a reassigned array")
pass_check("panel loaders come from a model synced in place, not a reassigned array")

if not re.search(
  r"if \(next && next\.kind === row\.entryKind && next\.keepLoaded === row\.keepLoaded && "
  r"next\.sourceUrl === row\.sourceUrl\) \{\s*delete wanted\[row\.pluginId\]",
  shell_qml,
):
  fail_check("a panel whose plugin still loads the same way keeps its loader")
pass_check("a panel whose plugin still loads the same way keeps its loader")

if not re.search(r"function unloadPanels\(\) \{[\s\S]*?panelEntryModel\.clear\(\)", shell_qml):
  fail_check("a full plugin reload still rebuilds every panel from fresh code")
pass_check("a full plugin reload still rebuilds every panel from fresh code")

if shell_qml.count("shell.syncPanelEntries()") != 2:
  fail_check("plugin changes and finished scans sync the panel entries")
pass_check("plugin changes and finished scans sync the panel entries")
