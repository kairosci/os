"""Ensure panel QML resolves commands through the supported command path."""

from __future__ import annotations

from base_test import ROOT, fail_check, pass_check


panels = ROOT / "src/shell/plugins/panels"
for path in panels.rglob("*.qml"):
  for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
    if "root.bar.archPath" in line or "/bin/arch-" in line:
      fail_check(f"panels do not resolve arch helpers through bar paths: {path}:{number}:{line}")

pass_check("panels avoid bar path resolution for arch helpers")
