"""Check the packaged Limine defaults and boot menu template."""

from __future__ import annotations

from base_test import ROOT, fail_check, pass_check


packaged_defaults = (ROOT / "etc/limine-entry-tool.d/arch-defaults.conf").read_text(encoding="utf-8")
required_defaults = {
  'KERNEL_CMDLINE[default]+=" initramfs_async=0"': "packaged Limine defaults keep Plymouth alive at the LUKS prompt",
  'KERNEL_CMDLINE[default]+=" systemd.tty.term.console=dumb"': "packaged Limine defaults keep PID 1 from waiting on the console",
  'BOOT_ORDER="linux-t2, linux, linux-*, *, *fallback, Snapshots"': "packaged Limine defaults protect T2 Macs and prefer the exact os kernel elsewhere",
}
for value, description in required_defaults.items():
  if value not in packaged_defaults.splitlines():
    fail_check(description)
  pass_check(description)

limine_template = (ROOT / "default/limine/limine.conf").read_text(encoding="utf-8").splitlines()
for value, description in (
  ("timeout: 1", "Limine template waits 1 second for a key at boot"),
  ("quiet: yes", "Limine template keeps the boot menu quiet until a key is pressed"),
):
  if value not in limine_template:
    fail_check(description)
  pass_check(description)
