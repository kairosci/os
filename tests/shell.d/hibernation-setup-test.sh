#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
mkdir -p "$tmpdir/bin"

cmdline_file="$tmpdir/kernel.cmdline"
printf '%s\n' 'root=/dev/mapper/root rw resume=/dev/old resume_offset=123 quiet' >"$cmdline_file"
python3 "$ROOT/installer/boot/update-kernel-cmdline.py" "$cmdline_file" set \
  resume=/dev/mapper/root resume_offset=456 rtc_cmos.use_acpi_alarm=1
grep -Fxq 'root=/dev/mapper/root rw quiet resume=/dev/mapper/root resume_offset=456 rtc_cmos.use_acpi_alarm=1' \
  "$cmdline_file" || fail "setting kernel arguments replaces old values and preserves unrelated options"
python3 "$ROOT/installer/boot/update-kernel-cmdline.py" "$cmdline_file" remove resume resume_offset
grep -Fxq 'root=/dev/mapper/root rw quiet rtc_cmos.use_acpi_alarm=1' "$cmdline_file" ||
  fail "removing kernel arguments preserves unrelated options"
pass "systemd-boot kernel command line parameters can be updated safely"

cat >"$tmpdir/bin/bootctl" <<'EOF'
#!/bin/bash
printf 'Current Boot Loader:\n    Product: %s\n' "$ARCH_TEST_BOOTLOADER"
EOF

cat >"$tmpdir/bin/mkinitcpio" <<'EOF'
#!/bin/bash
printf 'mkinitcpio %s\n' "$*" >>"$ARCH_TEST_REBUILD_LOG"
EOF

cat >"$tmpdir/bin/limine-mkinitcpio" <<'EOF'
#!/bin/bash
printf 'limine-mkinitcpio %s\n' "$*" >>"$ARCH_TEST_REBUILD_LOG"
EOF

cat >"$tmpdir/bin/arch-cmd-present" <<'EOF'
#!/bin/bash
[[ $1 == "limine-mkinitcpio" && ${ARCH_TEST_HAVE_LIMINE:-0} == "1" ]]
EOF
chmod +x "$tmpdir/bin/"*

ARCH_TEST_REBUILD_LOG="$tmpdir/rebuild.log" \
  ARCH_TEST_BOOTLOADER=systemd-boot \
  PATH="$tmpdir/bin:$ROOT/src/cli:$PATH" \
  "$ROOT/src/cli/arch-kernel-rebuild"
grep -Fxq 'mkinitcpio -P' "$tmpdir/rebuild.log" ||
  fail "systemd-boot rebuilds the mkinitcpio UKI preset"

ARCH_TEST_REBUILD_LOG="$tmpdir/rebuild.log" \
  ARCH_TEST_BOOTLOADER=Limine \
  ARCH_TEST_HAVE_LIMINE=1 \
  PATH="$tmpdir/bin:$ROOT/src/cli:$PATH" \
  "$ROOT/src/cli/arch-kernel-rebuild"
grep -Fxq 'limine-mkinitcpio ' "$tmpdir/rebuild.log" ||
  fail "Limine keeps its own kernel image rebuild path"

ARCH_TEST_REBUILD_LOG="$tmpdir/rebuild.log" \
  ARCH_TEST_BOOTLOADER=Limine \
  PATH="$tmpdir/bin:$ROOT/src/cli:$PATH" \
  "$ROOT/src/cli/arch-kernel-rebuild"
(( $(grep -cx 'mkinitcpio -P' "$tmpdir/rebuild.log") == 2 )) ||
  fail "mkinitcpio remains available without the optional Limine integration"
pass "kernel image rebuilds follow the active bootloader"

if [[ ! -f /sys/power/image_size ]]; then
  skip "hibernation is unavailable; skipping setup prompt test"
  exit 0
fi

mkdir -p "$tmpdir/bin"

cat >"$tmpdir/bin/arch-cmd-missing" <<'EOF'
#!/bin/bash
exit 1
EOF

cat >"$tmpdir/bin/grep" <<'EOF'
#!/bin/bash
exit 1
EOF

cat >"$tmpdir/bin/free" <<'EOF'
#!/bin/bash
if [[ ${LC_ALL:-} == "C" ]]; then
  printf 'Mem: 31Gi 1Gi 30Gi\n'
else
  printf '内存： 31Gi 1Gi 30Gi\n'
fi
EOF

cat >"$tmpdir/bin/gum" <<'EOF'
#!/bin/bash
printf '%s\n' "$*" >"$PROMPT_LOG"
exit 1
EOF

chmod +x "$tmpdir/bin/"*

env -u LC_ALL PROMPT_LOG="$tmpdir/prompt" PATH="$tmpdir/bin:$PATH" \
  "$ROOT/src/cli/arch-hibernation-setup"

[[ $(<"$tmpdir/prompt") == "confirm Use 31Gi on boot drive to make hibernation available?" ]] ||
  fail "hibernation setup reads memory size independently of the user's locale"
pass "hibernation setup reads memory size independently of the user's locale"
