"""Check that the Battle.net launcher remains installer-only."""

from __future__ import annotations

from base_test import ROOT, fail_check, pass_check


default_launcher = ROOT / "assets/applications/battlenet.desktop"
installer_launcher = ROOT / "default/applications/battlenet.desktop"
installer = (ROOT / "src/arch/commands/arch-install-gaming-battlenet").read_text(encoding="utf-8")

if default_launcher.exists():
  fail_check("Battle.net launcher is not part of default application refresh")
if not installer_launcher.is_file():
  fail_check("Battle.net launcher template is available to the installer")
if "$AP/default/applications/battlenet.desktop" not in installer:
  fail_check("Battle.net installer installs the launcher from the installer-only template")

pass_check("Battle.net launcher is only installed by the Battle.net installer")
