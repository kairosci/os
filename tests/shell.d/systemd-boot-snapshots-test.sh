#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

sync_script="$ROOT/install/boot/sync-systemd-boot-snapshots.sh"
snapper_plugin="$ROOT/install/boot/systemd-boot-snapper-plugin.sh"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
esp="$scratch/esp"
config="$scratch/limine.conf"
mkdir -p "$esp/machine-id/limine_history" "$esp/loader/entries"
touch "$esp/machine-id/limine_history/linux-1.efi"
touch "$esp/machine-id/limine_history/linux-2.efi"

run_sync() {
  ARCH_LIMINE_CONF="$config" ARCH_SYSTEMD_BOOT_ESP="$esp" \
    bash "$sync_script" >/dev/null
}

cat >"$config" <<'CONF'
//Snapshots
///12 │ 2026-10-24 12:00:00
////linux
path: boot():/machine-id/limine_history/linux-1.efi
cmdline: cryptdevice=PARTUUID=1234:root root=/dev/mapper/root rootflags=subvol=@/.snapshots/12/snapshot rw
///13 │ 2026-10-24 13:00:00
////linux
path: boot():/machine-id/limine_history/linux-2.efi
cmdline: cryptdevice=PARTUUID=1234:root root=/dev/mapper/root rootflags=subvol=@/.snapshots/13/snapshot rw
/
CONF

run_sync
arch_entry="$esp/loader/entries/arch-snapshot-12-arch.conf"
recovery_entry="$esp/loader/entries/arch-snapshot-13-recovery.conf"
[[ -f $arch_entry ]] || fail "an Arch snapshot gets a systemd-boot entry"
[[ -f $recovery_entry ]] || fail "the recovery kernel gets a systemd-boot entry"
grep -Fxq 'title   Snapshot #12 (2026-10-24 12:00:00) - Arch Linux' "$arch_entry" ||
  fail "the Arch snapshot title is clear"
grep -Fxq 'uki     /machine-id/limine_history/linux-1.efi' "$arch_entry" ||
  fail "the entry points to its archived UKI"
grep -Fxq 'options cryptdevice=PARTUUID=1234:root root=/dev/mapper/root rootflags=subvol=@/.snapshots/12/snapshot rw' "$arch_entry" ||
  fail "the entry keeps the snapshot root command line"
grep -Fxq 'title   Snapshot #13 (2026-10-24 13:00:00) - Recovery kernel' "$recovery_entry" ||
  fail "the old Arch kernel is presented as a recovery kernel"
pass "snapshot UKIs are translated into branded systemd-boot entries"

cat >"$config" <<'CONF'
//Snapshots
/
CONF
run_sync
[[ ! -e $arch_entry && ! -e $recovery_entry ]] ||
  fail "stale snapshot entries are removed after a successful empty sync"
pass "stale snapshot entries are removed after a successful empty sync"

if (( $(id -u) == 0 )); then
  echo "ok - a missing snapshot section leaves existing entries untouched # SKIP"
else
  cat >"$config" <<'CONF'
//Snapshots
///12 │ 2026-10-24 12:00:00
////linux
path: boot():/machine-id/limine_history/linux-1.efi
cmdline: cryptdevice=PARTUUID=1234:root root=/dev/mapper/root rootflags=subvol=@/.snapshots/12/snapshot rw
/
CONF
  run_sync
  cat >"$config" <<'CONF'
// no Snapper section
CONF
  if run_sync; then
    fail "a missing snapshot section is not treated as an empty snapshot list"
  fi
  [[ -f $arch_entry ]] || fail "a missing section does not remove existing generated entries"
  pass "a missing snapshot section leaves existing entries untouched"
fi

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

objcopy() {
  [[ $1 == "-O" && $2 == "binary" && $3 == "--only-section=.cmdline" ]] || return 1
  cp "$kernel_test/embedded-cmdline" "${@: -1}"
}

export ARCH_PATH="$ROOT"
export ARCH_SYSTEMD_BOOT_KERNEL_ESP="$kernel_test/esp"
export ARCH_MKINITCPIO_CONFIG_DIR="$kernel_test/etc/mkinitcpio.d"
export ARCH_KERNEL_CMDLINE_FILE="$kernel_test/etc/kernel/cmdline"
export ARCH_KERNEL_UKI="$kernel_test/esp/EFI/Linux/os_linux.efi"
export ARCH_KERNEL_PRESET_TEMPLATE="$ROOT/default/mkinitcpio/linux.preset"
export ARCH_MKINITCPIO_DEFAULT_PRESET=/usr/share/mkinitcpio/hook.preset
export ARCH_HW_X86_HELPER="$kernel_test/arch-hw-x86"
source "$ROOT/install/config/systemd-boot-kernel.sh"
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
source "$ROOT/install/config/systemd-boot-kernel.sh"
cmp -s "$ROOT/default/mkinitcpio/linux.preset" "$kernel_test/etc/mkinitcpio.d/linux.preset" ||
  fail "the previous shipped preset is updated to the current Arch kernel path"
pass "the previous shipped Arch preset is upgraded without overwriting custom presets"

printf '%s\n' 'user preset' >"$kernel_test/etc/mkinitcpio.d/linux.preset"
if source "$ROOT/install/config/systemd-boot-kernel.sh"; then
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
  ARCH_MACHINE_ID=test-machine \
  ARCH_ARCH_UKI="$plugin_test/boot/EFI/Linux/os_linux.efi" \
  ARCH_TEST_BOOT_PRODUCT="$plugin_test/boot-product" \
  PATH="$plugin_test/bin:$PATH" \
  bash "$snapper_plugin" create-snapshot-post / 0 14
[[ ! -e $plugin_test/boot/loader/entries/arch-snapshot-14.conf ]] ||
  fail "a Limine boot does not activate systemd-boot snapshot entries"
[[ -e $plugin_test/systemd/units/arch-snapshot-entries.path ]] ||
  fail "a Limine boot leaves its systemd-boot snapshot converter intact"
printf '%s\n' systemd-boot >"$plugin_test/boot-product"
ARCH_SNAPSHOTS_BOOT_ROOT="$plugin_test/boot" \
  ARCH_SNAPSHOTS_ROOT="$plugin_test/snapshots" \
  ARCH_MACHINE_ID=test-machine \
  ARCH_ARCH_UKI="$plugin_test/boot/EFI/Linux/os_linux.efi" \
  ARCH_TEST_BOOT_PRODUCT="$plugin_test/boot-product" \
  ARCH_SYSTEMD_UNIT_DIR="$plugin_test/systemd/units" \
  ARCH_SYSTEMD_LIBEXEC_DIR="$plugin_test/systemd/libexec" \
  ARCH_LIMINE_SNAPPER_PLUGIN="$plugin_test/limine-snapper-plugin" \
  ARCH_TEST_CMDLINE="$plugin_test/cmdline" \
  ARCH_TEST_CMDLINE_OUTPUT="$plugin_test/updated-cmdline" \
  ARCH_TEST_SYSTEMCTL_LOG="$plugin_test/systemctl.log" \
  PATH="$plugin_test/bin:$PATH" \
  bash "$snapper_plugin" create-snapshot-post / 0 14
plugin_uki="$plugin_test/boot/test-machine/arch-snapshots/snapshot-14-linux.efi"
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
  ARCH_MACHINE_ID=test-machine \
  ARCH_TEST_BOOT_PRODUCT="$plugin_test/boot-product" \
  ARCH_SYSTEMD_UNIT_DIR="$plugin_test/systemd/units" \
  ARCH_SYSTEMD_LIBEXEC_DIR="$plugin_test/systemd/libexec" \
  ARCH_TEST_SYSTEMCTL_LOG="$plugin_test/systemctl.log" \
  PATH="$plugin_test/bin:$PATH" \
  bash "$snapper_plugin" delete-snapshot-post / 0 14
[[ ! -e $plugin_uki && ! -e $plugin_entry ]] ||
  fail "deleting a Snapper snapshot removes its UKI and systemd-boot entry"
pass "Snapper creates and removes self-contained systemd-boot snapshot entries"

migration_test="$scratch/migration"
mkdir -p "$migration_test/bin" "$migration_test/esp/EFI/systemd"
printf '%s\n' loader >"$migration_test/esp/EFI/systemd/systemd-bootx64.efi"
cat >"$migration_test/bin/sudo" <<'SUDO'
#!/bin/bash
printf 'sudo %s\n' "$*" >>"$ARCH_TEST_COMMAND_LOG"
exec "$@"
SUDO
cat >"$migration_test/bin/bootctl" <<'BOOTCTL'
#!/bin/bash
printf 'bootctl %s\n' "$*" >>"$ARCH_TEST_COMMAND_LOG"
if [[ $* == *" list" ]]; then
  printf 'id: %s\n' "$ARCH_TEST_BOOT_ID"
fi
BOOTCTL
printf '#!/bin/bash\nexit 1\n' >"$migration_test/bin/arch-hw-x86"
chmod +x "$migration_test/bin/"*
if ARCH_PATH="$ROOT" \
  ARCH_SYSTEMD_BOOT_ESP="$migration_test/esp" \
  ARCH_TEST_COMMAND_LOG="$migration_test/commands.log" \
  ARCH_TEST_BOOT_ID=unrelated.efi \
  PATH="$migration_test/bin:$PATH" \
  bash "$ROOT/migrations/1792846494.sh" >/dev/null 2>&1; then
  fail "the systemd-boot migration refuses to select a missing Arch UKI"
fi
! grep -Fq 'set-default' "$migration_test/commands.log" ||
  fail "the systemd-boot migration does not set a default before verifying the Arch entry"
ARCH_PATH="$ROOT" \
  ARCH_SYSTEMD_BOOT_ESP="$migration_test/esp" \
  ARCH_TEST_COMMAND_LOG="$migration_test/commands.log" \
  ARCH_TEST_BOOT_ID=os_linux.efi \
  PATH="$migration_test/bin:$PATH" \
  bash "$ROOT/migrations/1792846494.sh" >/dev/null
grep -Fq 'bootctl --esp-path='"$migration_test/esp"' set-default os_linux.efi' \
  "$migration_test/commands.log" || fail "the systemd-boot migration selects the Arch UKI as default"
pass "the systemd-boot migration verifies and selects the Arch UKI"

default_migration_test="$scratch/default-migration"
mkdir -p "$default_migration_test/bin" "$default_migration_test/esp/EFI/systemd" \
  "$default_migration_test/esp/loader"
printf '%s\n' loader >"$default_migration_test/esp/EFI/systemd/systemd-bootx64.efi"
cat >"$default_migration_test/esp/loader/loader.conf" <<'CONF'
default opensuse-microos-6.19.11-1-default-4.conf
timeout 5
editor no
CONF
cat >"$default_migration_test/bin/sudo" <<'SUDO'
#!/bin/bash
exec "$@"
SUDO
cat >"$default_migration_test/bin/bootctl" <<'BOOTCTL'
#!/bin/bash
case "$*" in
  *" list") printf 'id: %s\n' "${ARCH_TEST_BOOT_ID:-os_linux.efi}" ;;
  *" set-default os_linux.efi") printf 'set-default %s\n' "$*" >>"$ARCH_TEST_COMMAND_LOG" ;;
  *) exit 99 ;;
esac
BOOTCTL
chmod +x "$default_migration_test/bin/"*
cp "$default_migration_test/esp/loader/loader.conf" "$default_migration_test/original-loader.conf"
: >"$default_migration_test/commands.log"
if ARCH_PATH="$ROOT" \
  ARCH_SYSTEMD_BOOT_ESP="$default_migration_test/esp" \
  ARCH_SYSTEMD_BOOT_LOADER_CONF="$default_migration_test/esp/loader/loader.conf" \
  ARCH_TEST_COMMAND_LOG="$default_migration_test/commands.log" \
  ARCH_TEST_BOOT_ID=opensuse.efi \
  PATH="$default_migration_test/bin:$PATH" \
  bash "$ROOT/migrations/1792848000.sh" >/dev/null 2>&1; then
  fail "the persistent default migration refuses to select a missing Arch UKI"
fi
cmp -s "$default_migration_test/original-loader.conf" "$default_migration_test/esp/loader/loader.conf" ||
  fail "the loader configuration is unchanged when the Arch UKI is missing"
! grep -Fq 'set-default' "$default_migration_test/commands.log" ||
  fail "the firmware default is unchanged when the Arch UKI is missing"
ARCH_PATH="$ROOT" \
  ARCH_SYSTEMD_BOOT_ESP="$default_migration_test/esp" \
  ARCH_SYSTEMD_BOOT_LOADER_CONF="$default_migration_test/esp/loader/loader.conf" \
  ARCH_TEST_COMMAND_LOG="$default_migration_test/commands.log" \
  PATH="$default_migration_test/bin:$PATH" \
  bash "$ROOT/migrations/1792848000.sh" >/dev/null
grep -Fxq 'default os_linux.efi' "$default_migration_test/esp/loader/loader.conf" ||
  fail "the persistent default selects the Arch UKI"
grep -Fxq 'timeout 5' "$default_migration_test/esp/loader/loader.conf" ||
  fail "the existing systemd-boot timeout is preserved"
grep -Fxq 'editor no' "$default_migration_test/esp/loader/loader.conf" ||
  fail "the existing systemd-boot editor setting is preserved"
grep -Fq 'set-default --esp-path=' "$default_migration_test/commands.log" ||
  fail "the firmware default also selects the Arch UKI"
pass "systemd-boot defaults are corrected from stale OpenSUSE entries without losing loader settings"

unset -f objcopy
unset ARCH_PATH ARCH_SYSTEMD_BOOT_KERNEL_ESP ARCH_MKINITCPIO_CONFIG_DIR
unset ARCH_KERNEL_CMDLINE_FILE ARCH_KERNEL_UKI ARCH_KERNEL_PRESET_TEMPLATE
unset ARCH_MKINITCPIO_DEFAULT_PRESET
unset ARCH_HW_X86_HELPER
