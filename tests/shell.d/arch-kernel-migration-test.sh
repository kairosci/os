#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

migration="$ROOT/migrations/1789325478.sh"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/bin" "$scratch/drop-ins"

export PATH="$scratch/bin:$ROOT/src/cli:$PATH"
export CALL_LOG="$scratch/calls"
export INSTALLED_PACKAGES="$scratch/packages"
export ARCH_KERNEL_LIMINE_CONF="$scratch/limine"
export ARCH_KERNEL_LIMINE_DROP_INS="$scratch/drop-ins"
export ARCH_KERNEL_REBUILD_MARKER="$scratch/state/1789325478"
kernel="linux"
boot_order='BOOT_ORDER="linux, linux-*, *, *fallback, Snapshots"'

# Exercise the real package helpers, including their post-install queries.
cat > "$scratch/bin/pacman" <<'SH'
#!/bin/bash
case "$1" in
  -Q) [[ $2 == -- ]] || exit 99; grep -Fxq -- "$3" "$INSTALLED_PACKAGES" ;;
  -S)
    printf 'pacman %s\n' "$*" >> "$CALL_LOG"
    [[ ${INSTALL_FAIL:-0} == "0" ]] || exit 1
    for arg in "$@"; do
      [[ $arg == -* ]] || printf '%s\n' "$arg" >> "$INSTALLED_PACKAGES"
    done
    ;;
  *) exit 99 ;;
esac
SH

cat > "$scratch/bin/sudo" <<'SH'
#!/bin/bash
printf 'sudo %s\n' "$*" >> "$CALL_LOG"
case "$1" in
  pacman | mkdir | touch | sed | tee | install | limine-mkinitcpio | limine-entry-tool) exec "$@" ;;
  *) exit 99 ;;
esac
SH

cat > "$scratch/bin/limine-mkinitcpio" <<'SH'
#!/bin/bash
[[ ${REBUILD_FAIL:-0} == "0" ]]
SH

cat > "$scratch/bin/limine-entry-tool" <<'SH'
#!/bin/bash
[[ $* == "--tree" ]] || exit 99
printf '%s\n' 'os' '  linux-ptl' '  linux-ptl-novrr-mm' '  linux-bore' '  linux-fallback' '  Snapshots'
if [[ ${MISSING_ENTRY:-0} == "0" ]]; then
  printf '%s\n' '  linux'
fi
SH

cat > "$scratch/bin/arch-state" <<'SH'
#!/bin/bash
[[ $* == "set reboot-required" ]] || exit 99
printf 'state %s\n' "$*" >> "$CALL_LOG"
SH

cat > "$scratch/bin/uname" <<'SH'
#!/bin/bash
case "$1" in
  -m) printf '%s\n' "${TEST_ARCH:-x86_64}" ;;
  -r) printf '%s\n' "${TEST_KERNEL_RELEASE:-7.2.5-arch1-1}" ;;
  *) exit 99 ;;
esac
SH

cat > "$scratch/bin/arch-notification-dismiss" <<'SH'
#!/bin/bash
exit 0
SH
chmod +x "$scratch/bin/"*

reset_fixture() {
  : > "$CALL_LOG"
  printf '%s\n' linux-ptl linux-ptl-headers > "$INSTALLED_PACKAGES"
  rm -f "$ARCH_KERNEL_REBUILD_MARKER" "$ARCH_KERNEL_LIMINE_DROP_INS/"*
  cat > "$ARCH_KERNEL_LIMINE_CONF" <<'CONF'
KERNEL_CMDLINE[default]="root=UUID=keep-me rw cryptdevice=UUID=keep-me:root"
BOOT_ORDER="*, *fallback, Snapshots"
ENABLE_UKI=yes
CONF
  cp "$ARCH_KERNEL_LIMINE_CONF" "$scratch/original-limine"
}

run_migration() {
  bash -euo pipefail "$migration" > "$scratch/output" 2>&1
}

assert_preferred() {
  grep -Fxq "$boot_order" "$1" || fail "os kernels are preferred in $1"
}

assert_skipped() {
  [[ ! -s $CALL_LOG ]] || fail "excluded systems do not change" "$(<"$CALL_LOG")"
  cmp -s "$ARCH_KERNEL_LIMINE_CONF" "$scratch/original-limine" || fail "excluded systems keep their boot settings"
  [[ ! -e $ARCH_KERNEL_REBUILD_MARKER ]] || fail "excluded systems do not get a completion marker"
}

for old_kernel in linux linux-lts linux-zen linux-ptl linux-ptl-novrr-mm; do
  reset_fixture
  printf '%s\n' "$old_kernel" "$old_kernel-headers" > "$INSTALLED_PACKAGES"
  run_migration
  grep -Fxq "$kernel" "$INSTALLED_PACKAGES" || fail "the generic kernel is installed"
  grep -Fxq "$kernel-headers" "$INSTALLED_PACKAGES" || fail "its headers are installed"
  grep -Fxq "$old_kernel" "$INSTALLED_PACKAGES" || fail "the previous kernel remains available"
  assert_preferred "$ARCH_KERNEL_LIMINE_CONF"
  pass "$old_kernel systems receive the generic os kernel and retain their recovery kernel"
done

for installed in linux-t2 $'linux-t2\nlinux\nlinux-ptl\nlinux'; do
  reset_fixture
  printf '%s\n' "$installed" > "$INSTALLED_PACKAGES"
  run_migration
  assert_skipped
done
pass "linux-t2 systems are skipped even with other kernels installed"

reset_fixture
TEST_KERNEL_RELEASE=7.2.5-arch1-T2 run_migration
assert_skipped
pass "a running T2 kernel is excluded even if its package is no longer installed"

reset_fixture
TEST_ARCH=aarch64 run_migration
assert_skipped
pass "ARM systems cannot receive an x86_64 kernel"

reset_fixture
printf '%s\n' linux-ptl-novrr-mm > "$INSTALLED_PACKAGES"
mkdir -p "$scratch/state" "$scratch/user-markers" "$scratch/arch/migrations"
export ARCH_PTL_REBUILD_MARKER="$scratch/state/1789095456"
export ARCH_MIGRATION_STATE="$scratch/user-markers"
touch "$ARCH_PTL_REBUILD_MARKER" "$ARCH_MIGRATION_STATE/1789095456.sh"
cp "$migration" "$scratch/arch/migrations/"
pending=$(ARCH_PATH="$scratch/arch" "$ROOT/src/cli/arch-migrate" --pending)
[[ $pending == "1789325478.sh" ]] || fail "the renamed migration is pending after completing the old migration"
ARCH_PATH="$scratch/arch" "$ROOT/src/cli/arch-migrate" > "$scratch/output" 2>&1
grep -Fxq "$kernel" "$INSTALLED_PACKAGES" || fail "the old completion markers cannot skip the generic kernel"
[[ -f $ARCH_KERNEL_REBUILD_MARKER && -f $ARCH_MIGRATION_STATE/1789325478.sh ]] || fail "new machine and user completion markers are recorded"
assert_preferred "$ARCH_KERNEL_LIMINE_CONF"
pass "users who completed the PTL migration run the renamed migration with fresh completion markers"

reset_fixture
for name in dell-xps-panther-lake zz-dell-xps-panther-lake; do
  printf '%s\n' 'BOOT_ORDER="linux-ptl*, *fallback, Snapshots"' > "$ARCH_KERNEL_LIMINE_DROP_INS/$name.conf"
done
cp "$ARCH_KERNEL_LIMINE_CONF" "$ARCH_KERNEL_LIMINE_DROP_INS/arch-defaults.conf"
run_migration
grep -Fxq "pacman -S --noconfirm --needed -- $kernel $kernel-headers" "$CALL_LOG" || fail "both new packages are installed"
grep -Fxq linux-ptl "$INSTALLED_PACKAGES" || fail "the old kernel is kept for recovery"
grep -Fxq linux-ptl-headers "$INSTALLED_PACKAGES" || fail "the old kernel headers are kept"
assert_preferred "$ARCH_KERNEL_LIMINE_CONF"
diff -u <(sed '/^BOOT_ORDER=/d; /^$/d' "$scratch/original-limine") \
  <(sed '/^BOOT_ORDER=/d; /^$/d' "$ARCH_KERNEL_LIMINE_CONF") || fail "kernel command line and unrelated settings are preserved"
grep -Fxq "sudo limine-mkinitcpio $kernel" "$CALL_LOG" || fail "the new kernel's boot image is rebuilt"
[[ -f $ARCH_KERNEL_REBUILD_MARKER ]] || fail "successful completion is recorded"
grep -Fxq 'state set reboot-required' "$CALL_LOG" || fail "the updater must offer a reboot when retaining the old kernel"
pass "new packages install, the central boot order is set, and the old kernel remains available"

: > "$CALL_LOG"
run_migration
[[ ! -s $CALL_LOG ]] || fail "another user's run does not repeat the machine-wide migration"
pass "repeat runs are a no-op after successful completion"

reset_fixture
printf '%s\n' "$kernel" >> "$INSTALLED_PACKAGES"
run_migration
grep -Fxq "$kernel-headers" "$INSTALLED_PACKAGES" || fail "missing headers install when the kernel is already present"
pass "a partially installed kernel gets its missing headers"

reset_fixture
printf '%s\n' "$kernel" "$kernel-headers" >> "$INSTALLED_PACKAGES"
run_migration
! grep -q '^pacman -S' "$CALL_LOG" || fail "already installed packages are not reinstalled"
assert_preferred "$ARCH_KERNEL_LIMINE_CONF"
pass "existing new packages still receive the config repair and boot rebuild"

reset_fixture
if INSTALL_FAIL=1 run_migration; then
  fail "package installation failure must fail the migration"
fi
cmp -s "$ARCH_KERNEL_LIMINE_CONF" "$scratch/original-limine" || fail "install failure leaves the config untouched"
! grep -q 'limine-mkinitcpio' "$CALL_LOG" || fail "install failure does not rebuild"
[[ ! -e $ARCH_KERNEL_REBUILD_MARKER ]] || fail "install failure stays pending"
pass "package failures leave the old boot setup intact and the migration pending"

reset_fixture
if REBUILD_FAIL=1 run_migration; then
  fail "boot rebuild failure must fail the migration"
fi
[[ ! -e $ARCH_KERNEL_REBUILD_MARKER ]] || fail "rebuild failure stays pending"
! grep -q '^state ' "$CALL_LOG" || fail "rebuild failure must not request a reboot"
assert_preferred "$ARCH_KERNEL_LIMINE_CONF"
: > "$CALL_LOG"
run_migration
grep -Fxq "sudo limine-mkinitcpio $kernel" "$CALL_LOG" || fail "retry must rebuild even after config and packages are repaired"
[[ -f $ARCH_KERNEL_REBUILD_MARKER ]] || fail "retry records successful completion"
pass "a failed rebuild is retried even after config and package changes succeeded"

reset_fixture
if MISSING_ENTRY=1 run_migration; then
  fail "a silently skipped kernel build must fail the migration"
fi
[[ ! -e $ARCH_KERNEL_REBUILD_MARKER ]] || fail "a missing boot entry stays pending"
! grep -q '^state ' "$CALL_LOG" || fail "a missing boot entry must not request a reboot"
run_migration
[[ -f $ARCH_KERNEL_REBUILD_MARKER ]] || fail "a missing boot entry can be repaired on retry"
pass "older os variants and fallback entries cannot satisfy generic kernel verification"

reset_fixture
cat >> "$ARCH_KERNEL_LIMINE_CONF" <<'CONF'
BOOT_ORDER="linux-*, *, *fallback, Snapshots"
  BOOT_ORDER = 'linux-lts, *, *fallback, Snapshots'
CONF
run_migration
assert_preferred "$ARCH_KERNEL_LIMINE_CONF"
[[ $(grep -c '^BOOT_ORDER=' "$ARCH_KERNEL_LIMINE_CONF") == "1" ]] || fail "only one boot order is written"
! grep -Eq '^[[:space:]]+BOOT_ORDER' "$ARCH_KERNEL_LIMINE_CONF" || fail "a later custom assignment cannot override first position"
pass "the exact generic kernel takes first position over previous PTL and custom orders"

reset_fixture
for name in arch-defaults dell-xps-panther-lake zz-dell-xps-panther-lake; do
  printf '%s\n' 'BOOT_ORDER="linux-ptl*, *fallback, Snapshots"' > "$ARCH_KERNEL_LIMINE_DROP_INS/$name.conf"
done
printf '%s\n' 'ENABLE_SORT=yes' >> "$ARCH_KERNEL_LIMINE_DROP_INS/arch-defaults.conf"
cp "$ROOT/etc/limine-entry-tool.d/arch-defaults.conf" "$ARCH_KERNEL_LIMINE_DROP_INS/arch-defaults.conf.pacnew"
run_migration
effective_order=$(bash -c 'declare -A KERNEL_CMDLINE; for conf in "$1/"*.conf "$2"; do source "$conf"; done; printf "%s" "$BOOT_ORDER"' -- "$ARCH_KERNEL_LIMINE_DROP_INS" "$ARCH_KERNEL_LIMINE_CONF")
[[ $effective_order == "linux, linux-*, *, *fallback, Snapshots" ]] || fail "the central config wins over old and customized drop-ins"
grep -Fxq 'ENABLE_SORT=yes' "$ARCH_KERNEL_LIMINE_DROP_INS/arch-defaults.conf" || fail "custom packaged settings survive"
cmp -s "$ROOT/etc/limine-entry-tool.d/arch-defaults.conf" \
  "$ARCH_KERNEL_LIMINE_DROP_INS/arch-defaults.conf.pacnew" || fail "the pacnew is left for the administrator to merge"
pass "the central boot order overrides legacy drop-ins and pacnew files without rewriting them"

reset_fixture
rm "$ARCH_KERNEL_LIMINE_CONF"
run_migration
assert_preferred "$ARCH_KERNEL_LIMINE_CONF"
pass "a missing central config is created with the exact kernel first"

retirement_test="$scratch/retirement"
mkdir -p "$retirement_test/bin" \
  "$retirement_test/modules/7.2.11-arch1-1"
cat >"$retirement_test/bin/arch-hw-x86" <<'SH'
#!/bin/bash
[[ ${TEST_X86:-1} == "1" ]]
SH
cat >"$retirement_test/bin/bootctl" <<'SH'
#!/bin/bash
[[ $1 == status && $2 == --no-pager ]] || exit 99
printf 'Current Boot Loader:\n    Product: %s\n' "${TEST_BOOTLOADER:-Limine}"
SH
cat >"$retirement_test/bin/uname" <<'SH'
#!/bin/bash
[[ $1 == -r ]] || exit 99
printf '%s\n' 7.2.11-arch1-1
SH
cat >"$retirement_test/bin/arch-pkg-drop" <<'SH'
#!/bin/bash
printf 'drop %s\n' "$*" >>"$CALL_LOG"
SH
chmod +x "$retirement_test/bin/"*

run_retirement() {
  env \
    PATH="$retirement_test/bin:$ROOT/src/cli:$PATH" \
    ARCH_KERNEL_MODULES_DIR="$retirement_test/modules" \
    CALL_LOG="$retirement_test/calls" \
    "$@" bash -euo pipefail "$ROOT/migrations/1792850007.sh" >"$retirement_test/output" 2>&1
}

run_original_retirement() {
  env \
    PATH="$retirement_test/bin:$ROOT/src/cli:$PATH" \
    ARCH_KERNEL_MODULES_DIR="$retirement_test/modules" \
    CALL_LOG="$retirement_test/calls" \
    "$@" bash -euo pipefail "$ROOT/migrations/1792848227.sh" >"$retirement_test/output" 2>&1
}

: >"$retirement_test/calls"
if run_original_retirement env TEST_BOOTLOADER=Limine; then
  fail "the original retired-kernel migration defers before systemd-boot is active"
else
  [[ $? == 75 ]] || fail "the original retired-kernel migration uses the deferred status"
fi
[[ ! -s $retirement_test/calls ]] || fail "the original migration leaves the kernel installed under Limine"
pass "the original kernel cleanup defers without blocking independent migrations"

: >"$retirement_test/calls"
printf '%s\n' linux >"$retirement_test/modules/7.2.11-arch1-1/pkgbase"
if run_original_retirement env TEST_BOOTLOADER=systemd-boot; then
  fail "the original retired-kernel migration defers while linux is running"
else
  [[ $? == 75 ]] || fail "the original retired-kernel migration defers the old running kernel"
fi
[[ ! -s $retirement_test/calls ]] || fail "the original migration keeps the running kernel installed"
pass "the original kernel cleanup waits for the Arch linux kernel"

: >"$retirement_test/calls"
printf '%s\n' linux >"$retirement_test/modules/7.2.11-arch1-1/pkgbase"
run_original_retirement env TEST_BOOTLOADER=systemd-boot
grep -Fxq 'drop linux linux-headers' "$retirement_test/calls" ||
  fail "the original migration removes the retired kernel after Arch linux boots"
pass "the original kernel cleanup completes after the Arch linux kernel boots"

: >"$retirement_test/calls"
if run_retirement env TEST_BOOTLOADER=Limine; then
  fail "the retired kernel cannot be removed before systemd-boot is running"
fi
[[ ! -s $retirement_test/calls ]] || fail "Limine boot keeps the existing kernel"
pass "the old kernel stays installed until systemd-boot is active even when the user cannot read the ESP"

: >"$retirement_test/modules/7.2.11-arch1-1/pkgbase"
printf '%s\n' linux >"$retirement_test/modules/7.2.11-arch1-1/pkgbase"
if run_retirement env TEST_BOOTLOADER=systemd-boot; then
  fail "systemd-boot with the old kernel cannot remove that running kernel"
fi
[[ ! -s $retirement_test/calls ]] || fail "the retired kernel stays while it is running"
pass "the old kernel stays installed unless the running pkgbase is Arch linux"

printf '%s\n' linux >"$retirement_test/modules/7.2.11-arch1-1/pkgbase"
run_retirement env TEST_BOOTLOADER=systemd-boot
grep -Fxq 'drop linux linux-headers' "$retirement_test/calls" ||
  fail "the retired kernel and headers are removed after the Arch kernel boots"
pass "the retired kernel is removed after systemd-boot runs the Arch linux kernel"

uki_test="$scratch/uki"
mkdir -p "$uki_test/bin" "$uki_test/modules/7.2.11-arch1-1"
cat >"$uki_test/bin/arch-hw-x86" <<'SH'
#!/bin/bash
exit 0
SH
cat >"$uki_test/bin/bootctl" <<'SH'
#!/bin/bash
printf 'bootctl %s\n' "$*" >>"$CALL_LOG"
case "$1" in
  status) printf 'Current Boot Loader:\n    Product: %s\n' "${TEST_BOOTLOADER:-systemd-boot}" ;;
  list)
    printf '%s\n' 'type: UKI' 'title: Arch Linux (7.2.11-arch1-1) (os_linux.efi) (default)' 'id: os_linux.efi'
    ;;
  set-default)
    [[ $2 == os_linux.efi ]] || exit 99
    ;;
  *) exit 99 ;;
esac
SH
cat >"$uki_test/bin/uname" <<'SH'
#!/bin/bash
[[ $1 == -r ]] || exit 99
printf '%s\n' 7.2.11-arch1-1
SH
cat >"$uki_test/bin/sudo" <<'SH'
#!/bin/bash
printf 'sudo %s\n' "$*" >>"$CALL_LOG"
if [[ $1 == env ]]; then
  printf 'configure-systemd-boot-kernel\n' >>"$CALL_LOG"
  exit 0
fi
exec "$@"
SH
cat >"$uki_test/bin/objcopy" <<'SH'
#!/bin/bash
[[ $1 == -O && $2 == binary && $3 == --only-section=.osrel ]] || exit 99
if [[ -e $UKI_TEST_BUILT ]]; then
  printf 'NAME="Arch Linux"\nID=arch\n' >"$5"
else
  printf 'NAME="os"\nID=os\n' >"$5"
fi
SH
cat >"$uki_test/bin/mkinitcpio" <<'SH'
#!/bin/bash
[[ $* == -P ]] || exit 99
printf 'mkinitcpio %s\n' "$*" >>"$CALL_LOG"
[[ ${UKI_TEST_REBUILD_FAIL:-0} == "0" ]] || exit 1
touch "$UKI_TEST_BUILT"
SH
chmod +x "$uki_test/bin/"*
printf '%s\n' linux >"$uki_test/modules/7.2.11-arch1-1/pkgbase"
printf '%s\n' 'NAME="Arch Linux"' 'ID=arch' >"$uki_test/os-release"

run_uki_migration() {
  env \
    PATH="$uki_test/bin:$ROOT/src/cli:$PATH" \
    ARCH_PATH="$ROOT" \
    ARCH_KERNEL_MODULES_DIR="$uki_test/modules" \
    ARCH_OS_RELEASE_FILE="$uki_test/os-release" \
    ARCH_ARCH_UKI="$uki_test/os_linux.efi" \
    CALL_LOG="$uki_test/calls" \
    UKI_TEST_BUILT="$uki_test/built" \
    "$@" bash -euo pipefail "$ROOT/migrations/1792850923.sh" >"$uki_test/output" 2>&1
}

: >"$uki_test/calls"
if run_uki_migration env TEST_BOOTLOADER=Limine; then
  fail "the UKI identity must not change until systemd-boot is running"
fi
! grep -q '^sudo ' "$uki_test/calls" || fail "Limine boot must not run privileged UKI changes"
pass "the Arch UKI migration waits until systemd-boot is active"

: >"$uki_test/calls"
printf '%s\n' linux >"$uki_test/modules/7.2.11-arch1-1/pkgbase"
if run_uki_migration; then
  fail "the UKI identity must not change while the old kernel is running"
fi
! grep -q '^sudo ' "$uki_test/calls" || fail "the old kernel must not run privileged UKI changes"
pass "the Arch UKI migration waits until the Arch kernel is running"

: >"$uki_test/calls"
printf '%s\n' linux >"$uki_test/modules/7.2.11-arch1-1/pkgbase"
run_uki_migration
grep -Fxq 'configure-systemd-boot-kernel' "$uki_test/calls" || fail "the systemd-boot kernel preset must be refreshed"
grep -Fxq 'mkinitcpio -P' "$uki_test/calls" || fail "stale UKI metadata must trigger a rebuild"
grep -Fxq 'sudo bootctl set-default os_linux.efi' "$uki_test/calls" || fail "the Arch UKI must be selected as the default"
pass "stale UKI branding is rebuilt and the Arch UKI becomes the default"

: >"$uki_test/calls"
run_uki_migration
grep -Fxq 'mkinitcpio -P' "$uki_test/calls" || fail "a repeated migration must keep the UKI in a recoverable state"
grep -Fxq 'sudo bootctl set-default os_linux.efi' "$uki_test/calls" || fail "the Arch default is reasserted on repeat runs"
pass "repeated runs preserve Arch metadata and reselect the Arch UKI"

rm -f "$uki_test/built"
: >"$uki_test/calls"
if run_uki_migration env UKI_TEST_REBUILD_FAIL=1; then
  fail "a UKI rebuild failure must leave the migration pending"
fi
! grep -q 'bootctl set-default' "$uki_test/calls" || fail "failed UKI rebuilds cannot change the default"
pass "a failed Arch UKI rebuild stays pending and leaves boot defaults untouched"
