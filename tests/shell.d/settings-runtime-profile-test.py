"""Check that every runtime settings profile entry exists in the source."""

from __future__ import annotations

import re

from base_test import ROOT, fail_check, pass_check


profile = ROOT / "default/settings-runtime-profile"
if not profile.is_file():
  fail_check("the source marks itself for the arch-settings recipe")
text = profile.read_text(encoding="utf-8")
listed = set(re.findall(r"(?:^|[ \t])((?:etc|default)/[^,\s]*)", text))
if not listed:
  fail_check("the runtime profile lists its files")
for path in listed:
  if not (ROOT / path.rstrip("/")).exists():
    fail_check(f"the runtime profile lists an existing file: {path}")
pass_check("every file the runtime profile lists exists in the source")

if "arch-hw-platform" not in (ROOT / "etc/mkinitcpio.conf.d/00-arch-hooks.conf").read_text(encoding="utf-8"):
  fail_check("the HOOKS baseline asks the platform")
if "modinfo" not in (ROOT / "etc/mkinitcpio.conf.d/thunderbolt_module.conf").read_text(encoding="utf-8"):
  fail_check("thunderbolt is added only where the kernel has the module")
if "zram-generator" not in (ROOT / "installer/arch-aarch64.packages").read_text(encoding="utf-8").splitlines():
  fail_check("aarch64 installs the zram generator the zram drop-in needs")
pass_check("the profile's runtime decisions are in place")
