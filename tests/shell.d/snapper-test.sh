#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

template="$ROOT/default/snapper/root"
limine_defaults="$ROOT/etc/limine-entry-tool.d/arch-defaults.conf"
limine_notify_autostart="$ROOT/config/autostart/limine-snapper-notify.desktop"

grep -Fx 'NUMBER_CLEANUP="yes"' "$template" >/dev/null
grep -Fx 'NUMBER_LIMIT="5"' "$template" >/dev/null
grep -Fx 'TIMELINE_CREATE="no"' "$template" >/dev/null
! grep -Eq '^TIMELINE_(CLEANUP|LIMIT_)' "$template" || fail "Snapper template keeps timeline cleanup details out of the default config"
grep -Fx 'MAX_SNAPSHOT_ENTRIES=6' "$limine_defaults" >/dev/null || fail "Limine allows for a snapshot created before Snapper cleanup"
pass "Snapper and Limine retain update snapshots without a transient limit mismatch"

grep -Fx '[Desktop Entry]' "$limine_notify_autostart" >/dev/null
grep -Fx 'Hidden=true' "$limine_notify_autostart" >/dev/null
pass "Limine Snapper warning notifier is disabled by default"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

fake_bin="$test_tmp/bin"
mkdir -p "$fake_bin"

cat >"$fake_bin/snapper" <<'STUB'
#!/bin/bash
printf 'snapper %s\n' "$*" >>"$TEST_LOG"
STUB
chmod +x "$fake_bin/snapper"

cat >"$fake_bin/systemctl" <<'STUB'
#!/bin/bash
printf 'systemctl %s\n' "$*" >>"$TEST_LOG"
STUB
chmod +x "$fake_bin/systemctl"

: >"$test_tmp/calls.log"

TEST_LOG="$test_tmp/calls.log" \
PATH="$fake_bin:$PATH" \
ARCH_SNAPPER_CONFIGURE_TEST=1 \
ARCH_PATH="$ROOT" \
ARCH_SNAPPER_CONFIG_PATH="$test_tmp/etc/snapper/configs/root" \
ARCH_SNAPPER_CONF_PATH="$test_tmp/etc/conf.d/snapper" \
  python3 -I "$ROOT/src/arch/python/installer/system_setup/snapper_setup.py" >/dev/null

cmp -s "$template" "$test_tmp/etc/snapper/configs/root" || fail "snapshot configure installs the os Snapper template"
grep -Fx 'SNAPPER_CONFIGS="root"' "$test_tmp/etc/conf.d/snapper" >/dev/null || fail "snapshot configure writes /etc/conf.d/snapper"
grep -Fx 'systemctl disable --now snapper-timeline.timer' "$test_tmp/calls.log" >/dev/null || fail "snapshot configure disables timeline snapshots"
grep -Fx 'systemctl enable --now snapper-cleanup.timer' "$test_tmp/calls.log" >/dev/null || fail "snapshot configure enables cleanup"
grep -Fx 'systemctl disable --now limine-snapper-sync.service arch-snapshot-entries.path arch-snapshot-entries.service' "$test_tmp/calls.log" >/dev/null || fail "snapshot configure disables Limine sync"
pass "snapshot configure normalizes Snapper policy and services"

mkdir -p "$test_tmp/invalid/data/installer"
printf '%s\n' 'snapper: [' >"$test_tmp/invalid/data/installer/snapper-setup.yml"
set +e
ARCH_PATH="$test_tmp/invalid" python3 -I "$ROOT/src/arch/python/installer/system_setup/snapper_setup.py" \
  >"$test_tmp/invalid-output" 2>"$test_tmp/invalid-error"
config_status=$?
set -e
(( config_status == 78 )) || fail "snapshot configure reports malformed YAML at its command boundary" "$config_status"
grep -Fq 'Could not load or apply Snapper setup configuration' "$test_tmp/invalid-error" ||
  fail "snapshot configure explains malformed YAML"
! grep -Fq 'Traceback' "$test_tmp/invalid-error" || fail "snapshot configure does not leak a traceback"
pass "snapshot configure handles malformed YAML at its command boundary"

mkdir -p "$test_tmp/invalid/data/installer"
printf '%s\n' 'systemd_boot_snapshots: [' >"$test_tmp/invalid/data/installer/config-setup.yml"
set +e
ARCH_PATH="$test_tmp/invalid" python3 -I "$ROOT/src/arch/python/installer/system_setup/systemd_boot_snapshots.py" \
  >"$test_tmp/snapshots-invalid-output" 2>"$test_tmp/snapshots-invalid-error"
snapshots_config_status=$?
set -e
(( snapshots_config_status == 78 )) || fail "systemd-boot snapshots reports malformed configuration at its command boundary"
grep -Fq 'Could not load systemd-boot snapshot settings' "$test_tmp/snapshots-invalid-error" ||
  fail "systemd-boot snapshots explains malformed configuration"
! grep -Fq 'Traceback' "$test_tmp/snapshots-invalid-error" || fail "systemd-boot snapshots does not leak a traceback"
pass "systemd-boot snapshots handles malformed YAML at its command boundary"

setup_system="$ROOT/src/arch/commands/arch-apply-system"
grep -F 'system_setup/all.py' "$setup_system" >/dev/null ||
  fail "system setup runs the config phase"
grep -F 'src/arch/python/installer/system_setup/snapper_setup.py' "$ROOT/data/installer/system-setup.yml" >/dev/null ||
  fail "config phase normalizes Snapper"
pass "system setup normalizes Snapper during fresh installs"

# The PKGBUILDs live in the arch-pkgs checkout, wherever this machine keeps it.
if find_arch_pkgs; then
  pkgs_root=$ARCH_PKGS_ROOT
  settings_pkgbuild="$pkgs_root/arch-settings-dev/PKGBUILD"
  arch_pkgbuild="$pkgs_root/arch-dev/PKGBUILD"

  grep -F 'cp -a default/. "$pkgdir/usr/share/arch/default/"' "$settings_pkgbuild" >/dev/null || fail "arch-settings package bundles default/"
  grep -F 'install -Dm644 default/snapper/root \' "$settings_pkgbuild" >/dev/null || fail "arch-settings package installs Snapper template source"
  grep -F '"$pkgdir/etc/snapper/config-templates/arch"' "$settings_pkgbuild" >/dev/null || fail "arch-settings package installs Snapper template destination"
  grep -F "'snapper'" "$arch_pkgbuild" >/dev/null || fail "archctl package depends on snapper"
  grep -F "'limine-snapper-sync'" "$arch_pkgbuild" >/dev/null || fail "archctl package depends on limine-snapper-sync"
  grep -F 'cp -a install "$pkgdir/usr/share/arch/"' "$arch_pkgbuild" >/dev/null || fail "archctl package bundles install scripts"
  pass "arch-pkgs packages Snapper template and setup"
else
  skip "arch-pkgs packages Snapper: needs the arch-pkgs checkout; set ARCH_PKGS_PATH to it"
fi

# Same per-machine checkout problem as arch-pkgs, with the same rule: an
# ARCH_ISO_PATH override is the only place tried, and one that doesn't
# resolve fails rather than skips.
find_arch_iso_root() {
  local candidate
  local -a candidates

  if [[ -n ${ARCH_ISO_PATH:-} ]]; then
    candidates=("$ARCH_ISO_PATH")
  else
    candidates=(
      "$ROOT/../arch-iso"
      "$ROOT/../arch/arch-iso"
      "$ROOT/../../arch-iso"
      "$ROOT/../omacom/arch-iso"
      "$ROOT/../../omacom/arch-iso"
      "$HOME/Work/omacom/arch-iso"
    )
  fi

  for candidate in "${candidates[@]}"; do
    if [[ -d $candidate/configs ]]; then
      ARCH_ISO_ROOT=$(CDPATH= cd -- "$candidate" && pwd)
      return 0
    fi
  done

  [[ -z ${ARCH_ISO_PATH:-} ]] ||
    fail "ARCH_ISO_PATH names an arch-iso checkout" "no configs/ under $ARCH_ISO_PATH"
  return 1
}

if find_arch_iso_root; then
  iso_root=$ARCH_ISO_ROOT
  configurator="$iso_root/configs/airootfs/root/configurator"
  phases="$iso_root/configs/airootfs/usr/share/arch-iso/orchestrator/phases_impl.py"
  manifest="$iso_root/manifests/fresh-4-semantic.json"

  ! grep -F 'snapshot_config' "$configurator" >/dev/null || fail "ISO does not ask archinstall to create Snapper timeline config"

  # The phases/manifest assertions cover the newer ISO orchestrator structure.
  # Skip them when the checkout predates that layout.
  if [[ -f $phases && -f $manifest ]]; then
    ! grep -F '_configure_snapper_root' "$phases" >/dev/null || fail "ISO does not duplicate os Snapper setup"
    grep -F 'run_system_finalizer' "$phases" >/dev/null || fail "ISO runs packaged system setup"
    grep -F '/etc/systemd/system/timers.target.wants/snapper-cleanup.timer' "$manifest" >/dev/null || fail "fresh ISO manifest has snapper-cleanup timer enabled"
    ! grep -F '/etc/systemd/system/timers.target.wants/snapper-timeline.timer' "$manifest" >/dev/null || fail "fresh ISO manifest does not enable snapper timeline timer"
  fi
  pass "arch-iso delegates Snapper setup to packaged system setup"
else
  skip "arch-iso delegates Snapper setup: needs the arch-iso checkout; set ARCH_ISO_PATH to it"
fi
