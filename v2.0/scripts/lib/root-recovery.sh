#!/usr/bin/env bash

root_recovery_snapshot_id() {
    local cmdline
    cmdline=$(cat "${OS_BOOT_CMDLINE:-/proc/cmdline}") || return 1
    [[ "$cmdline" =~ rootflags=[^[:space:]]*subvol=/[^[:space:]]*/([1-9][0-9]*)/snapshot([[:space:]]|$) ]] || return 1
    printf '%s\n' "${BASH_REMATCH[1]}"
}

root_setup_persistent() {
    local filesystem
    filesystem=$(findmnt --noheadings --output FSTYPE --target /) || return 1
    [[ "$filesystem" != overlay && "$filesystem" != tmpfs ]] || return 1
    if root_recovery_snapshot_id >/dev/null; then
        return 1
    fi
}

root_recovery_shell() {
    local home background file directory
    home=$(getent passwd "$PRIMARY_USER" | cut -d: -f6) || return 1
    background=$(readlink -f "$home/.local/state/omarchy/current/background") || return 1
    [[ -f "$background" ]] || return 1
    if [[ "${OS_RESTORE_OMARCHY:-0}" == 1 || "${SETUP_SCOPE:-}" == desktop || "${SETUP_SCOPE:-}" == recovery ]]; then
        [[ ! -L "$home/.config" ]] || return 1
        for file in kitty/kitty.conf alacritty/alacritty.toml ghostty/config foot/foot.ini; do
            directory="$home/.config/${file%/*}"
            [[ ! -L "$directory" && ! -L "$home/.config/$file" && ! -L "$home/.config/$file.bak" ]] || return 1
            if [[ -d "$directory" ]]; then
                chown "$PRIMARY_USER:$PRIMARY_USER" "$directory" || return 1
            fi
            for directory in "$home/.config/$file" "$home/.config/$file.bak"; do
                [[ ! -f "$directory" ]] || chown "$PRIMARY_USER:$PRIMARY_USER" "$directory" || return 1
            done
        done
        user_as "$PRIMARY_USER" env "OMARCHY_PATH=${OMARCHY_PATH:-/usr/share/omarchy}" "$PROJECT_DIR/script/os-lua" restore-native || return 1
        omarchy_as "$PRIMARY_USER" restart terminal || return 1
    fi
    omarchy_as "$PRIMARY_USER" restart shell || return 1
    omarchy_as "$PRIMARY_USER" shell shell ping || return 1
    omarchy_as "$PRIMARY_USER" theme bg set "$background" || return 1
    log "recovery.shell_ready"
}

root_recovery_restore() {
    local snapshot backup user home destination backups="${OS_RESTORE_BACKUP_ROOT:-/var/lib/os/omarchy-restore}"
    snapshot=$(root_recovery_snapshot_id) || return 1
    command -v snapper >/dev/null || return 1
    for backup in "$backups"/*; do
        [[ -d "$backup" && ! -L "$backup" ]] || continue
        user=${backup##*/}
        [[ "$user" =~ ^[a-z_][a-z0-9_-]*\$?$ ]] || return 1
        home=$(getent passwd "$user" | cut -d: -f6) || return 1
        [[ -d "$home" && ! -L "$home" ]] || return 1
        [[ $(findmnt --noheadings --output FSTYPE --target "$home") == btrfs ]] || return 1
        destination="$home/.local/state/os/recovery-backups/snapshot-$snapshot"
        tar -C "$backup" -cf - . | user_as "$user" bash -c '
            set -euo pipefail
            target="$1"
            if [[ -e "$target" || -L "$target" ]]; then
                [[ -d "$target" && ! -L "$target" && -f "$target/.complete" ]] || exit 1
                cat >/dev/null
                exit 0
            fi
            mkdir -p "${target%/*}"
            temporary=$(mktemp -d "$target.tmp.XXXXXX")
            trap '\''rm -rf "$temporary"'\'' EXIT
            tar --no-same-owner -xf - -C "$temporary"
            : > "$temporary/.complete"
            mv -T "$temporary" "$target"
        ' bash "$destination" || return 1
        log "recovery.backup" "$destination"
    done
    root_recovery_shell || return 1
    log "recovery.restore" "$snapshot"
    snapper -c root rollback || return 1
    log "recovery.reboot"
}
