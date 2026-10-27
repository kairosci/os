"""Replace dua without deleting a customized Disk Usage launcher."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

from base_test import ROOT, fail_check, pass_check, test_environment


MIGRATION = ROOT / "migrations/1791345484.py"
CONFIG = yaml.safe_load((ROOT / "data/migrations/1791345484.yml").read_text(encoding="utf-8"))


def run_case(callback) -> None:
  with tempfile.TemporaryDirectory(prefix="disktree-migration-") as temporary:
    scratch = Path(temporary)
    home = scratch / "home"
    data_home = home / "data"
    applications = data_home / "applications"
    applications.mkdir(parents=True)
    bin_dir = scratch / "bin"
    bin_dir.mkdir()
    log = scratch / "calls"

    commands = {
      "arch-i18n": 'printf "i18n:%s\\n" "$1" >>"$TEST_LOG"; printf "%s\\n" "$1"\n',
      "arch-pkg-add": 'printf "add:%s\\n" "$*" >>"$TEST_LOG"\n',
      "arch-pkg-drop": 'printf "drop:%s\\n" "$*" >>"$TEST_LOG"\n',
      "update-desktop-database": 'printf "database:%s\\n" "$*" >>"$TEST_LOG"\n',
    }
    for name, body in commands.items():
      command = bin_dir / name
      command.write_text(f"#!/bin/bash\nset -euo pipefail\n{body}", encoding="utf-8")
      command.chmod(0o755)

    environment = test_environment(
      ARCH_PATH=str(ROOT),
      HOME=str(home),
      XDG_DATA_HOME=str(data_home),
      PATH=f"{bin_dir}:{os.environ.get('PATH', '')}",
      TEST_LOG=str(log),
    )

    def run_migration() -> subprocess.CompletedProcess[str]:
      return subprocess.run(
        [sys.executable, "-I", str(MIGRATION)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
      )

    callback(scratch, applications, log, run_migration)


def generated_desktop_entry(icon: str) -> str:
  entry = CONFIG["desktop"]["generated_entries"][0].copy()
  entry["Icon"] = icon
  return "[Desktop Entry]\n" + "".join(f"{key}={value}\n" for key, value in entry.items())


def test_exact_launcher_is_removed_after_package_replacement(
  scratch: Path, applications: Path, log: Path, run_migration
) -> None:
  launcher = applications / CONFIG["paths"]["desktop_file"]
  launcher.write_text(generated_desktop_entry("disk-usage"), encoding="utf-8")
  result = run_migration()
  if result.returncode != 0:
    fail_check(f"migration succeeds: {result.stderr}")
  if launcher.exists():
    fail_check("the exact Arch-generated launcher is removed")
  if "migration.replaceDiskUsageWithDisktree" not in result.stdout or "migration.removeOldDiskUsageLauncher" not in result.stdout:
    fail_check(f"migration reports its localized actions: {result.stdout!r}")
  expected = [
    "i18n:migration.replaceDiskUsageWithDisktree",
    "add:disktree-bin",
    "drop:dua-cli",
    "i18n:migration.removeOldDiskUsageLauncher",
    f"database:{applications}",
  ]
  if log.read_text(encoding="utf-8").splitlines() != expected:
    fail_check(f"package and launcher actions stay ordered: {log.read_text(encoding='utf-8')}")
  pass_check("the exact old launcher is removed after installing Disktree")


def test_custom_launcher_and_symlink_are_preserved(scratch: Path, applications: Path, log: Path, run_migration) -> None:
  launcher = applications / CONFIG["paths"]["desktop_file"]
  custom = generated_desktop_entry("disk-usage").replace("Name=Disk Usage", "Name=My files")
  launcher.write_text(custom, encoding="utf-8")
  first = run_migration()
  if first.returncode != 0 or launcher.read_text(encoding="utf-8") != custom:
    fail_check("a customized launcher is preserved")

  launcher.unlink()
  target = scratch / "external.desktop"
  generated = generated_desktop_entry("disk-usage")
  target.write_text(generated, encoding="utf-8")
  launcher.symlink_to(target)
  second = run_migration()
  if second.returncode != 0 or not launcher.is_symlink() or target.read_text(encoding="utf-8") != generated:
    fail_check("a symlinked launcher and its target are preserved")
  if log.read_text(encoding="utf-8").count(f"database:{applications}") != 2:
    fail_check("the applications database refreshes after each package change")
  pass_check("custom and symlinked launchers stay untouched")


def test_missing_applications_directory_stays_missing(scratch: Path, applications: Path, log: Path, run_migration) -> None:
  applications.rmdir()
  result = run_migration()
  if result.returncode != 0:
    fail_check(f"migration succeeds without a user applications directory: {result.stderr}")
  if applications.exists():
    fail_check("migration does not create a user applications directory")
  if "database:" in log.read_text(encoding="utf-8"):
    fail_check("migration skips database refresh when the applications directory is absent")
  pass_check("no user applications directory is created")


def main() -> None:
  run_case(test_exact_launcher_is_removed_after_package_replacement)
  run_case(test_custom_launcher_and_symlink_are_preserved)
  run_case(test_missing_applications_directory_stays_missing)


if __name__ == "__main__":
  main()
