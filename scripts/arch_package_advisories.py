"""Report Arch advisories affecting package versions in the current repositories."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
from html.parser import HTMLParser
from typing import TypedDict, override
from urllib.error import URLError
from urllib.request import urlopen


TRACKER_URL = "https://security.archlinux.org/all.json"
ADVISORY_URL = "https://security.archlinux.org/{}"
PACKAGE_NAME = re.compile(r"[A-Za-z0-9@._+-]+")
ADVISORY_NAME = re.compile(r"AVG-[0-9]+")
CURRENT_VERSION = re.compile(r"^([A-Za-z0-9:._+~-]+)\s+\[[^\]]+\]$")
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


class _CurrentVersionParser(HTMLParser):
  def __init__(self) -> None:
    super().__init__()
    self.current_version: str | None = None
    self._in_row = False
    self._in_cell = False
    self._cell_parts: list[str] = []
    self._row_cells: list[str] = []

  @override
  def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    if tag == "tr":
      self._in_row = True
      self._row_cells = []
    elif tag == "td" and self._in_row:
      self._in_cell = True
      self._cell_parts = []

  @override
  def handle_data(self, data: str) -> None:
    if self._in_cell:
      value = data.strip()
      if value:
        self._cell_parts.append(value)

  @override
  def handle_endtag(self, tag: str) -> None:
    if tag == "td" and self._in_cell:
      self._row_cells.append(" ".join(self._cell_parts))
      self._in_cell = False
    elif tag == "tr" and self._in_row:
      if len(self._row_cells) == 2 and self._row_cells[0] == "Current":
        match = CURRENT_VERSION.fullmatch(self._row_cells[1])
        if match is not None:
          self.current_version = match.group(1)
      self._in_row = False


def parse_current_version(page: bytes) -> str | None:
  parser = _CurrentVersionParser()
  parser.feed(page.decode("utf-8"))
  return parser.current_version


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
      or ADVISORY_NAME.fullmatch(name) is None
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


def matching_advisories(
  packages: set[str],
  advisories: list[Advisory],
  current_versions: dict[str, str | None],
) -> list[tuple[str, Advisory]]:
  matches: list[tuple[str, Advisory]] = []
  for advisory in advisories:
    if advisory["status"] in {"Fixed", "Not affected"}:
      continue
    for package in sorted(packages.intersection(advisory["packages"])):
      current_version = current_versions.get(advisory["name"])
      if current_version is None or current_version == advisory["affected"]:
        matches.append((package, advisory))
  return sorted(matches, key=lambda match: (match[0], match[1]["name"]))


def historical_advisories(
  packages: set[str],
  advisories: list[Advisory],
  current_versions: dict[str, str | None],
) -> list[tuple[str, Advisory, str]]:
  records: list[tuple[str, Advisory, str]] = []
  for advisory in advisories:
    if advisory["status"] in {"Fixed", "Not affected"}:
      continue
    current_version = current_versions.get(advisory["name"])
    if current_version is None or current_version == advisory["affected"]:
      continue
    for package in sorted(packages.intersection(advisory["packages"])):
      records.append((package, advisory, current_version))
  return sorted(records, key=lambda record: (record[0], record[1]["name"]))


def _report(
  packages: set[str],
  advisories: list[Advisory],
  matches: list[tuple[str, Advisory]],
  historical: list[tuple[str, Advisory, str]],
  current_versions: dict[str, str | None],
) -> str:
  lines = [
    f"Arch security tracker entries: {len(advisories)}",
    f"Declared package names checked: {len(packages)}",
    f"Potential advisories affecting current packages: {len(matches)}",
    f"Historical tracker records excluded by current version: {len(historical)}",
  ]
  for package, advisory in matches:
    issues = ", ".join(advisory["issues"]) or "no CVE identifier listed"
    fixed = advisory["fixed"] or "not recorded"
    current_version = current_versions.get(advisory["name"])
    current = (
      f"current {current_version}"
      if current_version is not None
      else "current version unavailable; manual review required"
    )
    lines.append(
      f"{package}: {advisory['name']} — {advisory['status']}, {advisory['severity']}; "
      f"affected {advisory['affected']}, fixed {fixed}; {current}; {issues}"
    )
  for package, advisory, current_version in historical:
    issues = ", ".join(advisory["issues"]) or "no CVE identifier listed"
    lines.append(
      f"{package}: {advisory['name']} — affected {advisory['affected']}, "
      f"current {current_version}; excluded from current-package findings; {issues}"
    )
  lines.append(
    "Review notice: this scan compares Arch's current repository package version "
    "with the tracker's affected version. It does not audit already installed "
    "systems, pinned package versions, or third-party repositories."
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
    candidates = [
      advisory
      for advisory in advisories
      if advisory["status"] not in {"Fixed", "Not affected"}
      and packages.intersection(advisory["packages"])
    ]
    current_versions: dict[str, str | None] = {}
    for advisory_name in sorted({advisory["name"] for advisory in candidates}):
      with urlopen(ADVISORY_URL.format(advisory_name), timeout=30) as response:
        page = response.read(1_000_001)
      if len(page) > 1_000_000:
        raise ValueError(f"Arch advisory page exceeds 1 MB: {advisory_name}")
      current_versions[advisory_name] = parse_current_version(page)
    matches = matching_advisories(packages, advisories, current_versions)
    historical = historical_advisories(packages, advisories, current_versions)
  except (OSError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
    print(f"Arch package advisory scan failed: {error}", file=sys.stderr)
    return 1

  report = _report(packages, advisories, matches, historical, current_versions)
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
