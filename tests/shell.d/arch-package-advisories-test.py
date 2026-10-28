from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile

from base_test import ROOT, fail_check, pass_check


spec = importlib.util.spec_from_file_location(
  "arch_package_advisories", ROOT / "scripts/arch_package_advisories.py"
)
if spec is None or spec.loader is None:
  fail_check("Arch advisory scanner module can be loaded")
scanner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scanner
spec.loader.exec_module(scanner)


with tempfile.TemporaryDirectory() as temporary:
  installer = Path(temporary)
  (installer / "arch-base.packages").write_text(
    "# comment\nlinux\n  lua51 # package note\nlinux\n", encoding="utf-8"
  )
  (installer / "arch-aarch64.packages").write_text("linux-arm\n", encoding="utf-8")
  package_names = scanner.declared_packages(installer)
  if package_names != {"linux", "lua51", "linux-arm"}:
    fail_check("package manifests produce a deduplicated set without comments")
pass_check("package manifests produce a deduplicated set without comments")

tracker = [
  {
    "name": "AVG-1",
    "packages": ["linux", "unlisted"],
    "status": "Vulnerable",
    "severity": "Low",
    "affected": "1.0-1",
    "fixed": None,
    "issues": ["CVE-2026-0001"],
  },
  {
    "name": "AVG-2",
    "packages": ["lua51"],
    "status": "Fixed",
    "severity": "Critical",
    "affected": "1.0-1",
    "fixed": "1.0-2",
    "issues": ["CVE-2026-0002"],
  },
  {
    "name": "AVG-3",
    "packages": ["linux-arm"],
    "status": "Unknown",
    "severity": "Unknown",
    "affected": "1.0-1",
    "fixed": None,
    "issues": [],
  },
]
advisories = scanner.parse_tracker(tracker)
matches = scanner.matching_advisories({"linux", "lua51", "linux-arm"}, advisories)
if [(package, advisory["name"]) for package, advisory in matches] != [
  ("linux", "AVG-1"),
  ("linux-arm", "AVG-3"),
]:
  fail_check("only unresolved records matching declared packages are reported")
pass_check("only unresolved records matching declared packages are reported")

report = scanner._report({"linux"}, advisories, matches[:1])
if "do not prove" not in report or "CVE-2026-0001" not in report:
  fail_check("the advisory report states its version limitation and includes CVEs")
pass_check("the advisory report states its version limitation and includes CVEs")

try:
  scanner.parse_tracker([{"name": "invalid"}])
except ValueError:
  pass_check("malformed tracker entries fail closed")
else:
  fail_check("malformed tracker entries fail closed")

malicious = [dict(tracker[0], name="AVG-1\n::error::forged")]
try:
  scanner.parse_tracker(malicious)
except ValueError:
  pass_check("tracker control characters cannot forge workflow commands")
else:
  fail_check("tracker control characters cannot forge workflow commands")

if scanner._escape_workflow_command("percent%\r\n") != "percent%25%0D%0A":
  fail_check("workflow annotations escape command control characters")
pass_check("workflow annotations escape command control characters")
