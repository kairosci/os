#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
source "$SCRIPT_DIR/test_lib.sh"
source "$PROJECT_DIR/scripts/lib/i18n.sh"
source "$PROJECT_DIR/scripts/lib/root-recovery.sh"
locale_init
SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT
export OS_BOOT_CMDLINE="$SANDBOX/cmdline" OS_RESTORE_BACKUP_ROOT="$SANDBOX/backups"
PRIMARY_USER=tester
RECOVERY_HOME="$SANDBOX/home"
RECOVERY_TRACE="$SANDBOX/trace"
mkdir -p "$OS_RESTORE_BACKUP_ROOT/tester" "$RECOVERY_HOME"
mkdir -p "$RECOVERY_HOME/.local/state/omarchy/current"
printf 'wallpaper\n' > "$RECOVERY_HOME/wallpaper"
ln -s "$RECOVERY_HOME/wallpaper" "$RECOVERY_HOME/.local/state/omarchy/current/background"
printf 'original configuration\n' > "$OS_RESTORE_BACKUP_ROOT/tester/original"
printf 'root=/dev/mapper/root rootflags=subvol=/@ rw\n' > "$OS_BOOT_CMDLINE"
findmnt() {
    if [[ "${!#}" == / ]]; then
        printf '%s\n' "${RECOVERY_ROOT_FSTYPE:-btrfs}"
    else
        printf '%s\n' "${RECOVERY_HOME_FSTYPE:-btrfs}"
    fi
}
getent() { printf 'tester:x:1000:1000::%s:/bin/bash\n' "$RECOVERY_HOME"; }
user_as() { shift; HOME="$RECOVERY_HOME" XDG_CONFIG_HOME="$RECOVERY_HOME/.config" XDG_STATE_HOME="$RECOVERY_HOME/.local/state" "$@"; }
omarchy_as() {
    printf '%s\n' "$*" >> "$RECOVERY_TRACE"
    [[ ${RECOVERY_SHELL_FAIL:-0} == 0 ]]
}
snapper() {
    [[ -f "$RECOVERY_HOME/.local/state/os/recovery-backups/snapshot-17/.complete" ]] || return 1
    [[ "$*" == "-c root rollback" ]] || return 1
    printf 'restore\n' >> "$RECOVERY_TRACE"
    [[ ${RECOVERY_RESTORE_FAIL:-0} == 0 ]]
}
test_section "Persistent root recovery"
assert_true "normal Btrfs root permits provisioning" 'root_setup_persistent'
assert_false "temporary overlay root refuses provisioning" 'RECOVERY_ROOT_FSTYPE=overlay root_setup_persistent'
assert_false "temporary tmpfs root refuses provisioning" 'RECOVERY_ROOT_FSTYPE=tmpfs root_setup_persistent'
assert_false "normal boot cannot invoke snapshot restore" 'root_recovery_restore'
printf 'root=/dev/mapper/root rootflags=subvol=/@/.snapshots/17/snapshot rw\n' > "$OS_BOOT_CMDLINE"
assert_equal "snapshot ID is derived from the boot parameters" "$(root_recovery_snapshot_id)" 17
assert_false "snapshot boot refuses provisioning even without an overlay" 'root_setup_persistent'
assert_true "restore saves backups on persistent home before native recovery" 'root_recovery_restore && grep -qx "original configuration" "$RECOVERY_HOME/.local/state/os/recovery-backups/snapshot-17/original"'
assert_true "shell restart and IPC verification precede Snapper rollback" '[[ $(sed -n "1p" "$RECOVERY_TRACE") == "tester restart shell" && $(sed -n "2p" "$RECOVERY_TRACE") == "tester shell shell ping" && $(sed -n "3p" "$RECOVERY_TRACE") == "tester theme bg set $RECOVERY_HOME/wallpaper" && $(sed -n "4p" "$RECOVERY_TRACE") == restore ]]'
printf 'changed RAM configuration\n' > "$OS_RESTORE_BACKUP_ROOT/tester/original"
assert_true "retry preserves the first complete persistent backup" 'root_recovery_restore && grep -qx "original configuration" "$RECOVERY_HOME/.local/state/os/recovery-backups/snapshot-17/original"'
: > "$RECOVERY_TRACE"
assert_false "temporary home storage aborts recovery" 'RECOVERY_HOME_FSTYPE=tmpfs root_recovery_restore'
assert_true "temporary home storage cannot trigger native restore" '[[ ! -s "$RECOVERY_TRACE" ]]'
assert_false "failed shell reconciliation aborts root replacement" 'RECOVERY_SHELL_FAIL=1 root_recovery_restore'
assert_true "failed shell reconciliation leaves root replacement untouched" '! grep -qx restore "$RECOVERY_TRACE"'
assert_false "native restore errors propagate" 'RECOVERY_RESTORE_FAIL=1 root_recovery_restore'
assert_true "native restore failure preserves the persistent backup" 'grep -qx "original configuration" "$RECOVERY_HOME/.local/state/os/recovery-backups/snapshot-17/original"'
assert_false "an incomplete existing backup cannot be accepted" 'rm "$RECOVERY_HOME/.local/state/os/recovery-backups/snapshot-17/.complete" && root_recovery_restore'
printf 'rootflags=subvol=/@/.snapshots/not-a-number/snapshot\n' > "$OS_BOOT_CMDLINE"
assert_false "invalid snapshot ID is rejected" 'root_recovery_snapshot_id'

export OMARCHY_PATH="$SANDBOX/upstream"
mkdir -p "$OMARCHY_PATH"
printf 'native Omarchy logo\n' > "$OMARCHY_PATH/logo.txt"
printf 'native Omarchy icon\n' > "$OMARCHY_PATH/icon.txt"
for file in kitty/kitty.conf alacritty/alacritty.toml ghostty/config foot/foot.ini; do
    mkdir -p "$OMARCHY_PATH/config/${file%/*}"
    printf 'native Omarchy terminal\n' > "$OMARCHY_PATH/config/$file"
done
mkdir -p "$RECOVERY_HOME/.config/kitty"
printf 'previous terminal\n' > "$RECOVERY_HOME/.config/kitty/kitty.conf"
chown() { return 0; }
assert_true "desktop recovery restores native terminal configs with a persistent backup" 'SETUP_SCOPE=desktop root_recovery_shell && cmp "$OMARCHY_PATH/config/kitty/kitty.conf" "$RECOVERY_HOME/.config/kitty/kitty.conf" && grep -qx "previous terminal" "$RECOVERY_HOME/.local/state/os/desktop-defaults/kitty/kitty.conf"'
assert_true "repeated desktop recovery preserves the first terminal backup" 'SETUP_SCOPE=desktop root_recovery_shell && grep -qx "previous terminal" "$RECOVERY_HOME/.local/state/os/desktop-defaults/kitty/kitty.conf"'
assert_true "desktop recovery installs the KMono ASCII logo for screensaver and About" 'cmp "$PROJECT_DIR/data/component/application/desktop/kmono.txt" "$RECOVERY_HOME/.config/os/branding/screensaver.txt" && cmp "$PROJECT_DIR/data/component/application/desktop/kmono.txt" "$RECOVERY_HOME/.config/os/branding/about.txt"'
assert_true "desktop recovery installs the native Fastfetch layout with the KMono logo" 'cmp "$PROJECT_DIR/data/component/application/desktop/fastfetch.jsonc" "$RECOVERY_HOME/.config/fastfetch/config.jsonc" && grep -q "source.*os/branding/about.txt" "$RECOVERY_HOME/.config/fastfetch/config.jsonc" && grep -q "Hardware" "$RECOVERY_HOME/.config/fastfetch/config.jsonc" && grep -q "Software" "$RECOVERY_HOME/.config/fastfetch/config.jsonc"'
test_summary
