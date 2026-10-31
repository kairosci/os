# Arch update process

`archctl update` is the supported system update entry point. Pacman owns installed system files; user configuration remains user-owned and is refreshed only when the user explicitly runs `archctl refresh config` or the relevant `arch-refresh-*` command.

## State and coordination files

| Path | Owner | Purpose |
| --- | --- | --- |
| `${XDG_RUNTIME_DIR:-/tmp}/arch-update.lock` | user | Prevent overlapping update runs. |
| `${XDG_RUNTIME_DIR}/arch-update-stay-awake/` | user | Private inhibitor coordination state. |
| `/tmp/arch-update.log` | user | Transcript used by `arch-update-analyze-logs`. |
| `~/.local/state/arch/current/` | user | Generated active theme, selected theme name, and current background symlink. |
| `~/.local/state/arch/reboot-required` | user | Optional reboot marker checked by `arch-update-restart`. |
| `~/.local/state/arch/restart-*-required` | user | Optional component restart markers. |

## Raw pacman guard

The `arch` package installs an ALPM pre-transaction hook and `/usr/bin/arch-update-pacman-guard`. Direct full-system upgrades are rejected unless invoked by the update pipeline or explicitly allowed by the administrator. This keeps snapshots, conflict handling, boot verification, and restart checks together.

## Update flow

`archctl update` runs `arch-update`, which logs the session, acquires the update lock, confirms the operation, checks free space, prunes the package cache, takes a snapshot, refreshes the keyring, updates system packages, handles orphans and AUR packages, verifies the boot chain, runs the post-update hook, updates mise tools, and checks restart requirements. Sudo authorization is acquired for the transaction and revoked during cleanup, including on failure.

Updates do not rewrite files in user home directories. Pacman installs package-owned defaults and reports administrator edits through its normal `.pacnew`/`.pacsave` behavior. To overwrite a user config with the shipped default, the user explicitly runs `archctl refresh config <relative-path>`; that command creates a backup when the file changes.

The `arch.system-update` bar widget runs `archctl update available` at shell startup and every six hours. Clicking it opens the update flow in a tiled terminal.

## Channels and versions

`arch-channel-set <stable|rc|edge|dev>` selects a package repository or links the runtime to a git checkout. Platform-specific pacman templates live under `default/pacman/`; `installer/helpers/pacman.sh` installs the matching config and mirrorlist and backs up files during a channel change. A channel change refuses a platform/channel pair without both templates.

There is no runtime version file. `arch-version` derives the version from the installed package or linked checkout, while `archctl version channel` reads the active pacman configuration.
