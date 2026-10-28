"""Check DNS setup uses NetworkManager and retires old networkd state."""

from __future__ import annotations

from base_test import ROOT, fail_check, pass_check


dns = (ROOT / "src/arch/commands/arch-dns").read_text(encoding="utf-8")
hardware_network = (ROOT / "data/installer/hardware.yml").read_text(encoding="utf-8")

if "systemd-networkd" in dns:
  fail_check("arch-dns no longer restarts systemd-networkd")

for setting in (
  "NetworkManager/conf.d/20-arch-dns.conf",
  "[global-dns-domain-*]",
  "ipv4.ignore-auto-dns yes",
  "ipv4.ignore-auto-dns no",
  "nmcli device reapply",
  "nmcli general reload conf",
  "nmcli general reload dns-full",
):
  if setting not in dns:
    fail_check(f"arch-dns configures DNS through NetworkManager: missing {setting}")

if "nmcli general reload conf,dns-full" in dns:
  fail_check("arch-dns must not push DNS before reapplying active profiles")
pass_check("arch-dns configures DNS through NetworkManager")

for setting in ("systemd-networkd.service", "systemd-networkd.socket", "20-wlan.network", "arch-networkd-retired"):
  if setting not in hardware_network:
    fail_check(f"hardware setup retires archinstall networkd state: missing {setting}")
pass_check("hardware setup retires archinstall networkd state")
