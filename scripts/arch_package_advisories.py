"""Report unresolved Arch advisories matching declared package names."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from typing import TypedDict
from urllib.error import URLError
from urllib.request import urlopen


TRACKER_URL = "https://security.archlinux.org/all.json"
PACKAGE_NAME = re.compile(r"[A-Za-z0-9@._+-]+")
TRACKER_STATUSES = {"Fixed", "Not affected", "Vulnerable", "Unknown"}
SEVERITIES = {"Critical", "High", "Medium", "Low", "Unknown"}


class Advisory(TypedDict):
  name: str
  packages: list[str]
  status: str
  severity: str
  affected: str
  fixed: str | None
  issues: list[str]


def declared_packages(installer_dir: Path) -> set[str]:
  files = sorted(installer_dir.glob("arch-*.packages"))
  if not files:
    raise ValueError(f"No Arch package manifests found in {installer_dir}")

  packages: set[str] = set()
  for path in files:
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
      name = line.split("#", 1)[0].strip()
      if not name:
        continue
      if PACKAGE_NAME.fullmatch(name) is None:
        raise ValueError(f"Invalid package name in {path}:{line_number}: {name!r}")
      packages.add(name)
  return packages


def parse_tracker(payload: object) -> list[Advisory]:
  if not isinstance(payload, list):
    raise ValueError("Arch security tracker response must be a JSON list")

  parsed: list[Advisory] = []
  for index, row in enumerate(payload):
    if not isinstance(row, dict):
      raise ValueError(f"Arch security tracker entry {index} must be an object")
    name = row.get("name")
    packages = row.get("packages")
    status = row.get("status")
    severity = row.get("severity")
    affected = row.get("affected")
    fixed = row.get("fixed")
    issues = row.get("issues")
    if (
      not isinstance(name, str)
      or not isinstance(packages, list)
      or not all(isinstance(package, str) for package in packages)
      or not isinstance(status, str)
      or status not in TRACKER_STATUSES
      or not isinstance(severity, str)
      or severity not in SEVERITIES
      or not isinstance(affected, str)
      or (fixed is not None and not isinstance(fixed, str))
      or not isinstance(issues, list)
      or not all(isinstance(issue, str) for issue in issues)
    ):
      raise ValueError(f"Arch security tracker entry {index} has invalid fields")
    values = [name, status, severity, affected, *(packages), *(issues)]
    if fixed is not None:
      values.append(fixed)
    if any(any(ord(character) < 32 or ord(character) == 127 for character in value) for value in values):
      raise ValueError(f"Arch security tracker entry {index} contains control characters")
    parsed.append(
      {
        "name": name,
        "packages": packages,
        "status": status,
        "severity": severity,
        "affected": affected,
        "fixed": fixed,
        "issues": issues,
      }
    )
  return parsed


def matching_advisories(packages: set[str], advisories: list[Advisory]) -> list[tuple[str, Advisory]]:
  matches: list[tuple[str, Advisory]] = []
  for advisory in advisories:
    if advisory["status"] in {"Fixed", "Not affected"}:
      continue
    for package in sorted(packages.intersection(advisory["packages"])):
      matches.append((package, advisory))
  return sorted(matches, key=lambda match: (match[0], match[1]["name"]))


def _report(packages: set[str], advisories: list[Advisory], matches: list[tuple[str, Advisory]]) -> str:
  lines = [
    f"Arch security tracker entries: {len(advisories)}",
    f"Declared package names checked: {len(packages)}",
    f"Potential open advisories to review: {len(matches)}",
  ]
  for package, advisory in matches:
    issues = ", ".join(advisory["issues"]) or "no CVE identifier listed"
    fixed = advisory["fixed"] or "not recorded"
    lines.append(
      f"{package}: {advisory['name']} — {advisory['status']}, {advisory['severity']}; "
      f"affected {advisory['affected']}, fixed {fixed}; {issues}"
    )
  lines.append(
    "Review notice: package manifests list names without versions. Matches identify "
    "unresolved tracker records for review; they do not prove that a particular "
    "installed or future package version is vulnerable."
  )
  return "\n".join(lines)


def _escape_workflow_command(value: str) -> str:
  return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main() -> int:
  root = Path(__file__).resolve().parents[1]
  try:
    packages = declared_packages(root / "installer")
    with urlopen(TRACKER_URL, timeout=30) as response:
      body = response.read(10_000_001)
    if len(body) > 10_000_000:
      raise ValueError("Arch security tracker response exceeds 10 MB")
    payload = json.loads(body)
    advisories = parse_tracker(payload)
    matches = matching_advisories(packages, advisories)
  except (OSError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
    print(f"Arch package advisory scan failed: {error}", file=sys.stderr)
    return 1

  report = _report(packages, advisories, matches)
  print(report)
  summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
  if summary_path is not None and summary_path != "":
    with Path(summary_path).open("a", encoding="utf-8") as summary:
      summary.write("## Arch package advisory review\n\n")
      summary.write(report)
      summary.write("\n")
  for package, advisory in matches:
    print(
      "::warning title=Arch package advisory::"
      + _escape_workflow_command(
        f"{package}: {advisory['name']} {advisory['status']} {advisory['severity']}"
      )
    )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
