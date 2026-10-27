#!/usr/bin/python3

"""Check the installed ARP sysctl defaults and kernel keys."""

from __future__ import annotations

import re
from pathlib import Path

from base_test import fail_check, pass_check


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "etc/sysctl.d/90-arch-arp.conf"
SYSCTL = Path("/proc/sys/net/ipv4/conf")


def main() -> int:
  lines = CONFIG.read_text(encoding="utf-8").splitlines()
  settings = set(lines)

  for scope in ("all", "default"):
    for key, value, description in (
      ("arp_ignore", "1", "interfaces answer ARP only for their own address"),
      ("arp_announce", "2", "interfaces announce their own address"),
    ):
      label = f"{scope} {description}"
      if f"net.ipv4.conf.{scope}.{key}={value}" in settings:
        pass_check(label)
      else:
        fail_check(label)

  valid_setting = re.compile(
    r"net\.ipv4\.conf\.(?:all|default)\.arp_(?:ignore|announce)=[0-9]"
  )
  unexpected = [line for line in lines if line and not line.startswith("#") and not valid_setting.fullmatch(line)]
  if unexpected:
    fail_check("the file only sets the ARP keys")
  pass_check("the file only sets the ARP keys")

  if (SYSCTL / "all/arp_ignore").exists():
    if all((SYSCTL / path).exists() for path in ("all/arp_announce", "default/arp_ignore")):
      pass_check("the keys exist on this kernel")
    else:
      fail_check("the keys exist on this kernel")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
