"""Verify power supply detection through the installed command interface."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


COMMAND = ROOT / "src/commands/arch-power-present"


def write_supply(root: Path, name: str, supply_type: str, online: str) -> None:
  supply = root / name
  supply.mkdir(parents=True, exist_ok=True)
  (supply / "type").write_text(f"{supply_type}\n", encoding="utf-8")
  (supply / "online").write_text(f"{online}\n", encoding="utf-8")


def detects_power_supply(path: Path) -> bool:
  result = subprocess.run(
    [str(COMMAND)],
    check=False,
    env=test_environment(ARCH_POWER_SUPPLY_PATH=str(path)),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
  return result.returncode == 0


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary_directory:
    supplies = Path(temporary_directory)
    write_supply(supplies, "AC", "Mains", "0")
    write_supply(supplies, "USBC", "USB", "1")
    if not detects_power_supply(supplies):
      fail_check("power present detects online USB-C supply")
    pass_check("power present detects online USB-C supply")

    (supplies / "USBC/online").write_text("0\n", encoding="utf-8")
    if detects_power_supply(supplies):
      fail_check("power present rejects offline supplies")
    pass_check("power present rejects offline supplies")

    write_supply(supplies, "AC", "Mains", "1")
    if not detects_power_supply(supplies):
      fail_check("power present detects online mains supply")
    pass_check("power present detects online mains supply")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
