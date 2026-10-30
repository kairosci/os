"""Verify battery detection distinguishes built-in and peripheral batteries."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


COMMAND = [str(ROOT / "src/arch/commands/archctl"), "battery", "present"]


def write_supply(root: Path, name: str, supply_type: str, present: str, scope: str | None = None) -> Path:
  supply = root / name
  supply.mkdir(parents=True, exist_ok=True)
  (supply / "type").write_text(f"{supply_type}\n", encoding="utf-8")
  (supply / "present").write_text(f"{present}\n", encoding="utf-8")
  if scope is not None:
    (supply / "scope").write_text(f"{scope}\n", encoding="utf-8")
  return supply


def detects_battery(path: Path) -> bool:
  result = subprocess.run(
    COMMAND,
    check=False,
    env=test_environment(ARCH_POWER_SUPPLY_PATH=str(path)),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  return result.returncode == 0


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary_directory:
    supplies = Path(temporary_directory)
    write_supply(supplies, "macsmc-ac", "Mains", "1")
    battery = write_supply(supplies, "CMB0", "Battery", "1")
    if not detects_battery(supplies):
      fail_check("battery presence accepts a non-BAT native path")
    pass_check("battery presence accepts a non-BAT native path")

    (battery / "present").write_text("0\n", encoding="utf-8")
    if detects_battery(supplies):
      fail_check("battery presence rejects an absent battery")
    pass_check("battery presence rejects an absent battery")

    (battery / "present").write_text("1\n", encoding="utf-8")
    (battery / "scope").write_text("System\n", encoding="utf-8")
    write_supply(supplies, "hidpp_battery_0", "Battery", "1", "Device")
    if not detects_battery(supplies):
      fail_check("battery presence accepts a system battery beside a peripheral")
    pass_check("battery presence accepts a system battery beside a peripheral")

    shutil.rmtree(battery)
    if detects_battery(supplies):
      fail_check("battery presence ignores a peripheral device battery")
    pass_check("battery presence ignores a peripheral device battery")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
