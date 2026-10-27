#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

# The two setup leaves and first run call the platform's own setup through the
# real dispatcher: a Mac fixture with arch-mac's entrypoints, and x86.

hardware_leaf="$ROOT/src/python/installer/hardware/platform_setup.py"
user_leaf="$ROOT/src/python/installer_user/setup/platform.py"

[[ $(grep '^run_logged' "$ROOT/installer/hardware/all.sh" | tail -n 1) == 'run_logged "$ARCH_PATH/src/python/installer/hardware/platform_setup.py"' ]] ||
  fail "the platform's system setup is the last hardware leaf"
[[ $(grep '^  - setup/' "$ROOT/data/installer/user-setup.yml" | tail -n 1) == '  - setup/platform.py' ]] ||
  fail "the platform's user setup is the last user leaf"
pass "the platform's setup is the last leaf of hardware and of user setup"

require_platform_fixtures "platform setup on platform fixtures"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fake_platform "$tmp/apple" aarch64-apple
fake_platform "$tmp/x86" x86

lifecycle=$tmp/lifecycle
mkdir -p "$lifecycle/usr/lib/arch/mac" "$lifecycle/usr/lib/arch/mac-boot"
for entry in mac/setup-system mac/setup-user mac-boot/setup-boot; do
  operation=${entry#*/}
  cat >"$lifecycle/usr/lib/arch/$entry" <<SH
#!/bin/bash
{ printf '%s' "$operation"; (( \$# == 0 )) || printf ' %s' "\$@"; echo; } >>"$tmp/ran"
[[ ! -e $tmp/fail && ! -e $tmp/fail-$operation ]]
SH
  chmod 755 "$lifecycle/usr/lib/arch/$entry"
done
chmod -R go-w "$lifecycle"

# Sources a leaf as run_logged does, on a platform fixture.
leaf() {
  local platform=$1 script=$2
  shift 2
  rm -f "$tmp/ran"
  if [[ $script == *.py ]]; then
    env "$@" ARCH_PATH="$ROOT" ARCH_PROC_ROOT="$tmp/$platform/proc" ARCH_LIFECYCLE_ROOT="$lifecycle" \
      PATH="$tmp/$platform/bin:$ROOT/src/cli:$PATH" python3 -I "$script" >"$tmp/output" 2>&1
  else
    env "$@" ARCH_PROC_ROOT="$tmp/$platform/proc" ARCH_LIFECYCLE_ROOT="$lifecycle" \
      PATH="$tmp/$platform/bin:$ROOT/src/cli:$PATH" bash -eE -c 'source "$1"' bash "$script" >"$tmp/output" 2>&1
  fi
}

# ── system setup ─────────────────────────────────────────────────────────────

leaf apple "$hardware_leaf" || fail "apple: the system setup leaf runs" "$(cat "$tmp/output")"
[[ $(cat "$tmp/ran") == $'setup-boot\nsetup-system' ]] || fail "apple: an install or rerun runs setup-boot, then setup-system, with no argument" "$(cat "$tmp/ran")"
leaf apple "$hardware_leaf" ARCH_IMAGE_DEFERRED_HARDWARE=1 || fail "apple: the system setup leaf runs on an image's first boot"
[[ $(cat "$tmp/ran") == $'setup-boot image-first-boot\nsetup-system image-first-boot' ]] ||
  fail "apple: an image's first boot tells setup-boot and setup-system so" "$(cat "$tmp/ran")"
touch "$tmp/fail-setup-system"
if leaf apple "$hardware_leaf"; then
  fail "apple: a failed setup-system fails the leaf"
fi
[[ $(cat "$tmp/ran") == $'setup-boot\nsetup-system' ]] || fail "apple: setup-system ran after the boot setup and failed" "$(cat "$tmp/ran")"
rm -f "$tmp/fail-setup-system"
touch "$tmp/fail-setup-boot"
if leaf apple "$hardware_leaf"; then
  fail "apple: a failed setup-boot fails the leaf"
fi
[[ $(cat "$tmp/ran") == "setup-boot" ]] || fail "apple: setup-system waits for a boot setup that failed" "$(cat "$tmp/ran")"
rm -f "$tmp/fail-setup-boot"
mv "$lifecycle/usr/lib/arch/mac-boot/setup-boot" "$tmp/setup-boot.saved"
if leaf apple "$hardware_leaf"; then
  fail "apple: a Mac whose boot package lacks setup-boot fails the leaf instead of skipping its boot setup"
fi
grep -q "setup-boot on aarch64-apple needs arch-mac-boot" "$tmp/output" || fail "apple: the failure names the boot package" "$(cat "$tmp/output")"
mv "$tmp/setup-boot.saved" "$lifecycle/usr/lib/arch/mac-boot/setup-boot"
pass "apple: the system setup leaf runs arch-mac-boot's setup-boot, then arch-mac's setup-system, says when it is an image's first boot, and fails with either"

touch "$tmp/fail"
leaf x86 "$hardware_leaf" ARCH_IMAGE_DEFERRED_HARDWARE=1 || fail "x86: the system setup leaf is a no-op" "$(cat "$tmp/output")"
[[ ! -e $tmp/ran && ! -s $tmp/output ]] || fail "x86: the system setup leaf runs nothing and says nothing" "$(cat "$tmp/output")"
rm -f "$tmp/fail"
pass "x86: the system setup leaf is a no-op, even with Mac entrypoints on disk"

# ── user setup ───────────────────────────────────────────────────────────────

leaf apple "$user_leaf" ARCH_IMAGE_ROOT="$tmp/booted" || fail "apple: the user setup leaf runs" "$(cat "$tmp/output")"
[[ $(cat "$tmp/ran") == "setup-user" ]] || fail "apple: the user setup leaf runs setup-user" "$(cat "$tmp/ran" 2>/dev/null)"
touch "$tmp/fail"
if leaf apple "$user_leaf" ARCH_IMAGE_ROOT="$tmp/booted"; then
  fail "apple: a failed setup-user fails finalization's leaf"
fi
rm -f "$tmp/fail"

mkdir -p "$tmp/image/var/lib/arch/image"
: >"$tmp/image/var/lib/arch/image/target"
leaf apple "$user_leaf" ARCH_IMAGE_ROOT="$tmp/image" || fail "apple: the user setup leaf succeeds in an image build"
[[ ! -e $tmp/ran && $(cat "$tmp/output") == *"waits for first run on the machine"* ]] ||
  fail "apple: an image build leaves the platform's user setup to first run" "$(cat "$tmp/output")"
LANG=it_IT.UTF-8 leaf apple "$user_leaf" ARCH_IMAGE_ROOT="$tmp/image" || fail "apple: the deferred message is localized" "$(cat "$tmp/output")"
[[ $(cat "$tmp/output") == *"attende il primo avvio"* ]] || fail "apple: the image-build message uses Italian" "$(cat "$tmp/output")"
pass "apple: the user setup leaf runs arch-mac's setup-user, fails with it, and waits for the machine in an image build"

touch "$tmp/fail"
leaf x86 "$user_leaf" ARCH_IMAGE_ROOT="$tmp/booted" || fail "x86: the user setup leaf is a no-op" "$(cat "$tmp/output")"
[[ ! -e $tmp/ran && ! -s $tmp/output ]] || fail "x86: the user setup leaf runs nothing and says nothing" "$(cat "$tmp/output")"
rm -f "$tmp/fail"
pass "x86: the user setup leaf is a no-op, even with Mac entrypoints on disk"

# ── first run ────────────────────────────────────────────────────────────────

# First run on the machine runs setup-user once the session is up. Its failure
# leaves first run pending for the next login, as a failed finalization does.
first_bin=$tmp/first-bin
first_root=$tmp/arch
mkdir -p "$first_bin" "$tmp/home"
cat >"$first_bin/arch-done" <<'SH'
#!/bin/bash
case "$1:$2" in
  check:first-run-user) exit 1 ;;
  mark:first-run-user) touch "$FIRST_RUN_MARKER" ;;
esac
SH
for helper in arch-provision-user arch-hook-install arch-notification-wait; do
  printf '#!/bin/bash\nexit 0\n' >"$first_bin/$helper"
done
chmod +x "$first_bin"/*
mkdir -p "$first_root/src/python/installer_user/first_run" "$first_root/data/installer"
cp "$ROOT/src/python/installer_user/first_run/commands.py" \
  "$first_root/src/python/installer_user/first_run/commands.py"
cp "$ROOT/src/python/installer_user/first_run/orchestrator.py" \
  "$first_root/src/python/installer_user/first_run/orchestrator.py"
cp "$ROOT/data/installer/first-run.yml" "$first_root/data/installer/first-run.yml"
cat >"$first_bin/gsettings" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$GSETTINGS_LOG"
[[ ${GSETTINGS_FAIL:-0} == 0 ]]
SH
chmod +x "$first_bin/gsettings"
cat >"$first_bin/arch-audio-tuning" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$AUDIO_TUNING_LOG"
[[ ${AUDIO_TUNING_FAIL:-0} == 0 ]]
SH
cat >"$first_bin/arch-notification-send" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$NOTIFICATION_LOG"
[[ ${NOTIFICATION_FAIL:-0} == 0 ]]
SH
chmod +x "$first_bin/arch-audio-tuning" "$first_bin/arch-notification-send"
cat >"$first_bin/arch-input-method" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$INPUT_METHOD_LOG"
[[ ${INPUT_METHOD_FAIL:-0} == 0 ]]
SH
cat >"$first_bin/systemctl" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$SYSTEMCTL_LOG"
[[ ${SYSTEMCTL_FAIL_UNIT:-} != "${@: -1}" ]]
SH
chmod +x "$first_bin/arch-input-method" "$first_bin/systemctl"

first_run() {
  local platform=$1
  rm -f "$tmp/ran" "$tmp/first-run-marker" "$tmp/home/.local/state/arch/first-run.log"
  HOME="$tmp/home" ARCH_PATH="$first_root" FIRST_RUN_MARKER="$tmp/first-run-marker" GSETTINGS_LOG="$tmp/gsettings.log" AUDIO_TUNING_LOG="$tmp/audio-tuning.log" NOTIFICATION_LOG="$tmp/notifications.log" INPUT_METHOD_LOG="$tmp/input-method.log" SYSTEMCTL_LOG="$tmp/systemctl.log" \
    ARCH_PROC_ROOT="$tmp/$platform/proc" ARCH_LIFECYCLE_ROOT="$lifecycle" \
    PATH="$first_bin:$tmp/$platform/bin:$ROOT/src/cli:$PATH" "$ROOT/src/cli/arch-provision-first-run" >"$tmp/output" 2>&1
}

LANG=it_IT.UTF-8 first_run apple || fail "apple: first run finishes" "$(cat "$tmp/output")"
[[ $(cat "$tmp/ran") == "setup-user" && -e $tmp/first-run-marker ]] ||
  fail "apple: first run runs setup-user and completes" "$(cat "$tmp/home/.local/state/arch/first-run.log" 2>/dev/null)"
[[ $(stat -c '%a' "$tmp/home/.local/state/arch/first-run.log") == 600 ]] ||
  fail "first-run log is private to its owner" "$(stat -c '%a' "$tmp/home/.local/state/arch/first-run.log")"
grep -q 'Scopri le scorciatoie' "$tmp/notifications.log" || fail "first-run welcome notification uses the Italian YAML translation" "$(cat "$tmp/notifications.log")"
touch "$tmp/fail"
first_run apple || fail "apple: first run with a failing setup-user still runs its other steps"
[[ ! -e $tmp/first-run-marker ]] || fail "apple: a failed setup-user keeps first run pending"
grep -q "Failed: run the platform's user setup" "$tmp/home/.local/state/arch/first-run.log" ||
  fail "apple: first run logs the failed platform setup" "$(cat "$tmp/home/.local/state/arch/first-run.log")"
first_run x86 || fail "x86: first run finishes"
[[ ! -e $tmp/ran && -e $tmp/first-run-marker ]] || fail "x86: first run runs no platform setup and completes"
rm -f "$tmp/fail"
GSETTINGS_FAIL=1 first_run apple || fail "apple: first run continues when setting GTK primary paste fails"
[[ ! -e $tmp/first-run-marker ]] || fail "a failed GTK setup keeps first run pending"
grep -q 'Failed: set GTK primary paste' "$tmp/home/.local/state/arch/first-run.log" ||
  fail "a failed GTK setup is recorded in first-run log" "$(cat "$tmp/home/.local/state/arch/first-run.log")"
grep -q 'set org.gnome.desktop.interface gtk-theme Breeze-Dark' "$tmp/gsettings.log" ||
  fail "GNOME theme reads its setting from the packaged YAML" "$(cat "$tmp/gsettings.log")"
grep -q '^on$' "$tmp/audio-tuning.log" ||
  fail "speaker tuning uses its packaged YAML command" "$(cat "$tmp/audio-tuning.log")"
GSETTINGS_FAIL=0 AUDIO_TUNING_FAIL=1 first_run apple || fail "apple: first run continues when speaker tuning fails"
[[ ! -e $tmp/first-run-marker ]] || fail "a failed speaker setup keeps first run pending"
grep -q 'Failed: apply speaker tuning' "$tmp/home/.local/state/arch/first-run.log" ||
  fail "a failed speaker setup is recorded in first-run log" "$(cat "$tmp/home/.local/state/arch/first-run.log")"
grep -q '^set org.gnome.desktop.interface gtk-enable-primary-paste true$' "$tmp/gsettings.log" ||
  fail "GTK primary paste uses the packaged YAML setting" "$(cat "$tmp/gsettings.log")"

cat >"$first_bin/nm-online" <<'SH'
#!/bin/bash
case " $* " in
  *' -s '*) exit 0 ;;
  *' -x '*) [[ ${WIFI_CONNECTED:-0} == 1 ]] ;;
  *) [[ ${WIFI_WAIT_CONNECTED:-0} == 1 ]] ;;
esac
SH
cat >"$first_bin/checkupdates" <<'SH'
#!/bin/bash
exit "${CHECKUPDATES_STATUS:-2}"
SH
cat >"$first_bin/arch-update-available" <<'SH'
#!/bin/bash
exit "${CHECKOUT_UPDATE_STATUS:-1}"
SH
chmod +x "$first_bin/nm-online" "$first_bin/checkupdates" "$first_bin/arch-update-available"
LANG=it_IT.UTF-8 WIFI_CONNECTED=0 WIFI_WAIT_CONNECTED=0 ARCH_PATH="$first_root" NOTIFICATION_LOG="$tmp/notifications.log" \
  PATH="$first_bin:$PATH" python3 -I "$first_root/src/python/installer_user/first_run/commands.py" wifi_worker ||
  fail "offline first run notifies the user to configure Wi-Fi" "$(cat "$tmp/notifications.log")"
grep -q 'Configura il Wi-Fi' "$tmp/notifications.log" || fail "Wi-Fi notification uses its Italian YAML translation" "$(cat "$tmp/notifications.log")"
LANG=it_IT.UTF-8 WIFI_CONNECTED=1 CHECKUPDATES_STATUS=0 ARCH_PATH="$first_root" NOTIFICATION_LOG="$tmp/notifications.log" \
  PATH="$first_bin:$PATH" python3 -I "$first_root/src/python/installer_user/first_run/commands.py" wifi_worker ||
  fail "available updates produce a notification" "$(cat "$tmp/notifications.log")"
grep -q 'Aggiorna il sistema' "$tmp/notifications.log" || fail "update notification uses its Italian YAML translation" "$(cat "$tmp/notifications.log")"
if ! LANG=it_IT.UTF-8 INPUT_METHOD_FAIL=1 ARCH_PATH="$first_root" INPUT_METHOD_LOG="$tmp/user-units-input.log" SYSTEMCTL_LOG="$tmp/user-units-systemctl.log" \
  PATH="$first_bin:$PATH" python3 -I "$first_root/src/python/installer_user/first_run/commands.py" user_units >"$tmp/user-units.out" 2>&1; then
  fail "input-method defaults may fail without blocking user unit setup" "$(cat "$tmp/user-units.out")"
fi
grep -q "Configurazione del metodo di input rimandata" "$tmp/user-units.out" || fail "input-method fallback is localized from YAML" "$(cat "$tmp/user-units.out")"
grep -q '^--user enable --now arch-crash-watch.service$' "$tmp/user-units-systemctl.log" || fail "a failed optional setup does not prevent later units" "$(cat "$tmp/user-units-systemctl.log")"
if SYSTEMCTL_FAIL_UNIT=arch-sleep-lock.service ARCH_PATH="$first_root" SYSTEMCTL_LOG="$tmp/user-units-failure.log" \
  PATH="$first_bin:$PATH" python3 -I "$first_root/src/python/installer_user/first_run/commands.py" user_units >"$tmp/user-units.out" 2>&1; then
  fail "a failed systemd unit keeps first run pending"
fi
grep -q '^--user enable --now arch-crash-watch.service$' "$tmp/user-units-failure.log" || fail "unit failures do not skip the remaining service setup" "$(cat "$tmp/user-units-failure.log")"
pass "first run runs platform setup, applies configured desktop settings, and localizes welcome, Wi-Fi, and update notifications"
