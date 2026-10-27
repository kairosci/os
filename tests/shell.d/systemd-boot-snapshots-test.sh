#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

snapper_plugin="$ROOT/src/python/installer/boot/systemd_boot_snapper_plugin.py"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT

# The Arch kernel's mkinitcpio preset must keep its UKI command line and
# generate the same UKI that systemd-boot already selects.
kernel_test="$scratch/kernel"
mkdir -p "$kernel_test/esp/EFI/systemd" "$kernel_test/esp/EFI/Linux" \
  "$kernel_test/etc/kernel" "$kernel_test/etc/mkinitcpio.d"
printf '#!/bin/bash\nexit 0\n' >"$kernel_test/arch-hw-x86"
chmod +x "$kernel_test/arch-hw-x86"
printf 'systemd-boot\n' >"$kernel_test/esp/EFI/systemd/systemd-bootx64.efi"
printf 'kernel\n' >"$kernel_test/esp/EFI/Linux/os_linux.efi"
printf '%s\n' 'cryptdevice=PARTUUID=1234:root root=/dev/mapper/custom rootflags=subvol=@ rw' \
  >"$kernel_test/etc/kernel/cmdline"
printf '%s\n' 'cryptdevice=PARTUUID=1234:root root=/dev/mapper/root rootflags=subvol=@ rw resume=/dev/mapper/root quiet splash' \
  >"$kernel_test/embedded-cmdline"

mkdir -p "$kernel_test/bin"
cat >"$kernel_test/bin/objcopy" <<'OBJCOPY'
#!/bin/bash
[[ $1 == "-O" && $2 == "binary" && $3 == "--only-section=.cmdline" ]] || exit 1
cp "$ARCH_TEST_EMBEDDED_CMDLINE" "${@: -1}"
OBJCOPY
chmod +x "$kernel_test/bin/objcopy"

export ARCH_PATH="$ROOT"
export ARCH_SYSTEMD_BOOT_KERNEL_ESP="$kernel_test/esp"
export ARCH_MKINITCPIO_CONFIG_DIR="$kernel_test/etc/mkinitcpio.d"
export ARCH_KERNEL_CMDLINE_FILE="$kernel_test/etc/kernel/cmdline"
export ARCH_KERNEL_UKI="$kernel_test/esp/EFI/Linux/os_linux.efi"
export ARCH_KERNEL_PRESET_TEMPLATE="$ROOT/default/mkinitcpio/linux.preset"
export ARCH_MKINITCPIO_DEFAULT_PRESET=/usr/share/mkinitcpio/hook.preset
export ARCH_HW_X86_HELPER="$kernel_test/arch-hw-x86"
export ARCH_TEST_EMBEDDED_CMDLINE="$kernel_test/embedded-cmdline"
PATH="$kernel_test/bin:$PATH" python3 -I "$ROOT/src/python/installer/system_setup/systemd_boot_kernel.py"
cmdline=$(<"$kernel_test/etc/kernel/cmdline")
[[ $cmdline == *'root=/dev/mapper/custom'* ]] || fail "a custom systemd root parameter is preserved" "$cmdline"
[[ $cmdline == *'resume=/dev/mapper/root quiet splash'* ]] || fail "the UKI's additional boot parameters are carried into mkinitcpio" "$cmdline"
cmp -s "$ROOT/default/mkinitcpio/linux.preset" "$kernel_test/etc/mkinitcpio.d/linux.preset" ||
  fail "the Arch kernel mkinitcpio preset is installed"
! grep -q '^ALL_config=' "$kernel_test/etc/mkinitcpio.d/linux.preset" ||
  fail "the Arch kernel preset leaves mkinitcpio drop-in configs enabled"
mkdir -p "$kernel_test/modules/7.2.11-arch1-1" "$kernel_test/modules/7.2.8-arch"
printf '%s\n' linux >"$kernel_test/modules/7.2.11-arch1-1/pkgbase"
printf '%s\n' linux >"$kernel_test/modules/7.2.8-arch/pkgbase"
touch "$kernel_test/modules/7.2.11-arch1-1/vmlinuz" "$kernel_test/modules/7.2.8-arch/vmlinuz"
selected_kernel=$(ARCH_KERNEL_MODULES_DIR="$kernel_test/modules" bash -c 'source "$1"; printf "%s" "$ALL_kver"' -- "$ROOT/default/mkinitcpio/linux.preset")
[[ $selected_kernel == "$kernel_test/modules/7.2.11-arch1-1/vmlinuz" ]] ||
  fail "the Arch preset selects the kernel image for pkgbase linux" "$selected_kernel"
pass "the Arch kernel command line and UKI preset are prepared for systemd-boot"

cat >"$kernel_test/etc/mkinitcpio.d/linux.preset" <<'PRESET'
# mkinitcpio preset for Arch Linux on systemd-boot.

ALL_config="/etc/mkinitcpio.conf"
ALL_kver="/boot/vmlinuz-linux"
ALL_cmdline="/etc/kernel/cmdline"

PRESETS=('default' 'fallback')

default_uki="/boot/EFI/Linux/os_linux.efi"
fallback_uki="/boot/EFI/Linux/os_linux-fallback.efi"
fallback_options="-S autodetect"
PRESET
PATH="$kernel_test/bin:$PATH" python3 -I "$ROOT/src/python/installer/system_setup/systemd_boot_kernel.py"
cmp -s "$ROOT/default/mkinitcpio/linux.preset" "$kernel_test/etc/mkinitcpio.d/linux.preset" ||
  fail "the previous shipped preset is updated to the current Arch kernel path"
pass "the previous shipped Arch preset is upgraded without overwriting custom presets"

printf '%s\n' 'user preset' >"$kernel_test/etc/mkinitcpio.d/linux.preset"
if PATH="$kernel_test/bin:$PATH" python3 -I "$ROOT/src/python/installer/system_setup/systemd_boot_kernel.py"; then
  fail "a custom mkinitcpio preset is not overwritten"
fi
grep -Fxq 'user preset' "$kernel_test/etc/mkinitcpio.d/linux.preset" ||
  fail "the existing custom mkinitcpio preset is preserved"
pass "a custom mkinitcpio preset is preserved"

# Snapper must archive the Arch UKI at snapshot time and embed that snapshot's
# Btrfs subvolume in the copied UKI, so this boot path does not depend on Limine.
plugin_test="$scratch/plugin"
mkdir -p "$plugin_test/bin" "$plugin_test/boot/EFI/Linux" \
  "$plugin_test/boot/loader/entries" "$plugin_test/snapshots/14/snapshot" \
  "$plugin_test/systemd/units" "$plugin_test/systemd/libexec"
touch "$plugin_test/limine-snapper-plugin"
chmod +x "$plugin_test/limine-snapper-plugin"
printf '%s\n' 'fake UKI' >"$plugin_test/boot/EFI/Linux/os_linux.efi"
printf '%s\n' 'cryptdevice=PARTUUID=1234:root root=/dev/mapper/root rootflags=subvol=@ rw rootfstype=btrfs quiet' \
  >"$plugin_test/cmdline"
cat >"$plugin_test/snapshots/14/info.xml" <<'XML'
<snapshot><date>2026-10-24 12:34:56</date></snapshot>
XML
cat >"$plugin_test/bin/objcopy" <<'OBJCOPY'
#!/bin/bash
set -euo pipefail
if [[ $1 == "-O" && $2 == "binary" && $3 == "--only-section=.cmdline" ]]; then
  cp "$ARCH_TEST_CMDLINE" "${@: -1}"
elif [[ $1 == --update-section ]]; then
  section_file=${2#*=}
  cp "$section_file" "$ARCH_TEST_CMDLINE_OUTPUT"
else
  exit 1
fi
OBJCOPY
chmod +x "$plugin_test/bin/objcopy"
cat >"$plugin_test/bin/systemctl" <<'SYSTEMCTL'
#!/bin/bash
printf '%s\n' "$*" >>"$ARCH_TEST_SYSTEMCTL_LOG"
SYSTEMCTL
chmod +x "$plugin_test/bin/systemctl"
cat >"$plugin_test/bin/bootctl" <<'BOOTCTL'
#!/bin/bash
printf '%s\n' 'Current Boot Loader:' "    Product: $(<"$ARCH_TEST_BOOT_PRODUCT")"
BOOTCTL
chmod +x "$plugin_test/bin/bootctl"
printf '%s\n' Limine >"$plugin_test/boot-product"
touch "$plugin_test/systemd/units/arch-snapshot-entries.path" \
  "$plugin_test/systemd/units/arch-snapshot-entries.service" \
  "$plugin_test/systemd/libexec/arch-sync-systemd-boot-snapshots"
ARCH_SNAPSHOTS_BOOT_ROOT="$plugin_test/boot" \
  ARCH_SNAPSHOTS_ROOT="$plugin_test/snapshots" \
ARCH_MACHINE_ID=00112233445566778899aabbccddeeff \
  ARCH_ARCH_UKI="$plugin_test/boot/EFI/Linux/os_linux.efi" \
  ARCH_TEST_BOOT_PRODUCT="$plugin_test/boot-product" \
  PATH="$plugin_test/bin:$PATH" \
  python3 -I "$snapper_plugin" create-snapshot-post / 0 14
[[ ! -e $plugin_test/boot/loader/entries/arch-snapshot-14.conf ]] ||
  fail "a Limine boot does not activate systemd-boot snapshot entries"
[[ -e $plugin_test/systemd/units/arch-snapshot-entries.path ]] ||
  fail "a Limine boot leaves its systemd-boot snapshot converter intact"
printf '%s\n' systemd-boot >"$plugin_test/boot-product"
ARCH_SNAPSHOTS_BOOT_ROOT="$plugin_test/boot" \
  ARCH_SNAPSHOTS_ROOT="$plugin_test/snapshots" \
ARCH_MACHINE_ID=00112233445566778899aabbccddeeff \
  ARCH_ARCH_UKI="$plugin_test/boot/EFI/Linux/os_linux.efi" \
  ARCH_TEST_BOOT_PRODUCT="$plugin_test/boot-product" \
  ARCH_SYSTEMD_UNIT_DIR="$plugin_test/systemd/units" \
  ARCH_SYSTEMD_LIBEXEC_DIR="$plugin_test/systemd/libexec" \
  ARCH_LIMINE_SNAPPER_PLUGIN="$plugin_test/limine-snapper-plugin" \
  ARCH_TEST_CMDLINE="$plugin_test/cmdline" \
  ARCH_TEST_CMDLINE_OUTPUT="$plugin_test/updated-cmdline" \
  ARCH_TEST_SYSTEMCTL_LOG="$plugin_test/systemctl.log" \
  PATH="$plugin_test/bin:$PATH" \
  python3 -I "$snapper_plugin" create-snapshot-post / 0 14
plugin_uki="$plugin_test/boot/00112233445566778899aabbccddeeff/arch-snapshots/snapshot-14-linux.efi"
plugin_entry="$plugin_test/boot/loader/entries/arch-snapshot-14.conf"
[[ -s $plugin_uki && -s $plugin_entry ]] || fail "Snapper creates an archived UKI and systemd-boot entry"
[[ ! -e $plugin_test/systemd/units/arch-snapshot-entries.path &&
  ! -e $plugin_test/systemd/units/arch-snapshot-entries.service &&
  ! -e $plugin_test/systemd/libexec/arch-sync-systemd-boot-snapshots ]] ||
  fail "systemd-boot disables and removes the Limine-backed entry converter"
[[ ! -x $plugin_test/limine-snapper-plugin ]] ||
  fail "systemd-boot disables the legacy Limine Snapper plugin"
grep -Fxq 'disable --now arch-snapshot-entries.path arch-snapshot-entries.service' \
  "$plugin_test/systemctl.log" || fail "systemd-boot stops the old converter units"
grep -Fxq 'disable --now limine-snapper-sync.service' \
  "$plugin_test/systemctl.log" || fail "systemd-boot stops the Limine Snapper watcher"
grep -Fq 'rootflags=subvol=@/.snapshots/14/snapshot' "$plugin_test/updated-cmdline" ||
  fail "the archived UKI boots the matching Btrfs snapshot"
grep -Fxq 'title   Snapshot #14 (2026-10-24 12:34:56) - Arch Linux' "$plugin_entry" ||
  fail "the systemd-boot snapshot entry shows its date"
ARCH_SNAPSHOTS_BOOT_ROOT="$plugin_test/boot" \
  ARCH_SNAPSHOTS_ROOT="$plugin_test/snapshots" \
  ARCH_MACHINE_ID=00112233445566778899aabbccddeeff \
  ARCH_TEST_BOOT_PRODUCT="$plugin_test/boot-product" \
  ARCH_SYSTEMD_UNIT_DIR="$plugin_test/systemd/units" \
  ARCH_SYSTEMD_LIBEXEC_DIR="$plugin_test/systemd/libexec" \
  ARCH_TEST_SYSTEMCTL_LOG="$plugin_test/systemctl.log" \
  PATH="$plugin_test/bin:$PATH" \
  python3 -I "$snapper_plugin" delete-snapshot-post / 0 14
[[ ! -e $plugin_uki && ! -e $plugin_entry ]] ||
  fail "deleting a Snapper snapshot removes its UKI and systemd-boot entry"
pass "Snapper creates and removes self-contained systemd-boot snapshot entries"

ARCH_PATH="$ROOT" \
  ARCH_SNAPSHOTS_BOOT_ROOT=/tmp/attacker-boot \
  ARCH_SNAPSHOTS_ROOT=/tmp/attacker-snapshots \
  ARCH_MACHINE_ID=../../etc/shadow \
  python3 -I - "$snapper_plugin" <<'PY' || fail "the privileged Snapper plugin ignores environment-controlled paths"
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

module = runpy.run_path(sys.argv[1])
settings = module["load_settings"]()
with patch.object(module["os"], "geteuid", return_value=0):
  paths = module["runtime_paths"](settings)
assert paths["boot_root"] == settings["paths"]["boot_root"]["default"]
assert paths["snapshots_root"] == settings["paths"]["snapshots_root"]["default"]
assert paths["machine_id"] == Path(settings["paths"]["machine_id"]["source"]).read_text(encoding="utf-8").strip()
with patch.dict(module["os"].environ, {"LANG": "it_IT.UTF-8"}):
  assert module["message"](settings, "invalid_machine_id") == settings["messages"]["it"]["invalid_machine_id"]
PY
pass "the privileged Snapper plugin ignores environment-controlled paths"
