# Arch migrations

Read this before creating or changing migrations under `migrations/`.

Arch migrations are one-time repair scripts for existing installs. They are
used when a package update needs to change state that pacman cannot safely own by
itself.

## Migration model

New migrations live in:

```text
migrations/*.py
```

Existing `migrations/*.sh` files remain supported for late updaters and are
being converted incrementally. Python migrations run with `python3 -I`; legacy
shell migrations run with `bash -euo pipefail`. Both run as the current Arch
user through `arch-migrate`, normally during `archctl update`. A migration may
touch user/session state (`~/.config`, `~/.local`, user systemd,
browser/editor prefs, DBus/session state), and may also perform machine-wide
repairs when needed.

Completion state is per-user:

```text
~/.local/state/arch/migrations/<migration filename>
```

That means every user gets a chance to run every migration. Migrations run as the
user; privileged operations should invoke the appropriate helper or privilege
prompt themselves. Migrations must be idempotent: if one user already applied a
machine-wide repair, the same migration running for another user should detect
that and no-op.

## When migrations run

### During `archctl update`

`archctl update` is the normal update path. It runs package updates, then:

```bash
arch-migrate
arch-hook post-update
```

`arch-migrate` waits for any active pacman transaction to finish, then runs
all pending migrations for the current user in the visible update terminal.

### At login

Every graphical login starts `arch-migrate-notify.service` after
`graphical-session.target`. The notifier checks:

```bash
arch-migrate --pending
```

It stays silent while `archctl update` holds its lock, since that update applies
the pending migrations itself.

If that user has pending migrations, it shows a notification that opens a
terminal for:

```bash
arch-migrate
```

The notifier never runs migrations silently in the background.

This is what covers users who did not run the update themselves: someone who
bypassed the pacman guard with `sudo env ARCH_ALLOW_DIRECT_PACMAN=1 pacman
-Syu`, and any second user on the machine, whose migration markers are per-user
and therefore still missing after another user updated.

Login is the only trigger on purpose. Watching the packaged migration directory
also fires during a normal `archctl update`, which prompts for migrations that
`arch-migrate` is about to run in the visible update terminal.

### Manually

Users can safely run:

```bash
arch-migrate
```

at any time. Already-completed migrations are skipped.

## Inspecting pending migrations

Use:

```bash
arch-migrate --pending
```

Exit behavior:

- `0` — one or more migrations are pending
- non-zero — no migrations are pending

Output is one pending migration per line:

```text
1781158082.sh
```

## Creating a migration

Use the helper:

```bash
arch-dev-add-migration --no-edit
```

This creates a Python migration:

```text
migrations/<unix timestamp>.py
```

It also creates the companion values file at
`data/migrations/<unix timestamp>.yml`. Put migration-specific paths, package
names, commands, and other variable values there; keep Python code focused on
the steps that apply those values.

New migration format:

- File permissions must be `0644` (`-rw-r--r--`). The runner invokes Python
  directly, not through executable bits.
- No shebang line.
- Use `arch-i18n` for user-facing output.
- Use `ARCH_PATH` via `os.environ["ARCH_PATH"]` to reference the Arch directory.
- Be idempotent. Check existing state before changing it.
- Migrations are strictly ordered and synchronous. A migration that cannot finish must remain pending. Return the deferred status from `data/cli/migrate.yml` only when later migrations are independent; the runner then continues with them. Any other non-zero exit stops the queue, so later migrations are never marked complete against state an earlier migration has not established.
- Use helper commands such as `arch-cmd-present`, `arch-cmd-missing`,
  `arch-pkg-add`, `arch-pkg-drop`, `arch-pkg-present`, and
  `arch-pkg-missing` when appropriate.
- Never restart the Arch shell. `archctl update` restarts it unconditionally
  after migrations run, and the login-time shell already runs current code and
  hot-reloads `shell.json` edits.
- Raw `pacman`, `command -v`, and direct config edits are acceptable when
  needed for one-off repair work.

Example:

```python
from __future__ import annotations

import os
from pathlib import Path
import yaml


def main() -> int:
  config_path = Path(os.environ["ARCH_PATH"]) / "data/migrations" / f"{Path(__file__).stem}.yml"
  config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
  theme_link = Path.home() / config["paths"]["theme_link"]
  if not theme_link.is_symlink():
    return int(config["statuses"]["success"])

  current_target = config["paths"]["current_theme"]
  theme_link.unlink()
  theme_link.symlink_to(current_target)
  return int(config["statuses"]["success"])


if __name__ == "__main__":
  raise SystemExit(main())
```

## Testing migrations

Run a Python migration against a temporary home when possible:

```bash
HOME=$(mktemp -d) ARCH_PATH="$PWD" python3 -I migrations/<timestamp>.py
```

Legacy `.sh` migrations can still be run with `HOME=$(mktemp -d) bash -euo
pipefail migrations/<timestamp>.sh`.

To rerun a migration locally, remove its marker and run the migrator:

```bash
rm ~/.local/state/arch/migrations/<migration>.py
arch-migrate
```

Keep a dedicated test while the migration is still being written or bugfixed, if it calls an Arch helper whose interface can still change, or if it is a security-sensitive privileged repair (FIDO2, leftover installer artifacts, udev, sshd). Once a one-shot rewrite has shipped in a tagged release and is frozen, drop the test even when that rewrite used sudo, pacman, or limine-mkinitcpio. Keep the migration itself for late-updaters. Tests of `arch-migrate`, the login notifier, and `arch-upgrade-to-quattro` stay.

Arch 4.0 is upgraded through `src/cli/arch-upgrade-to-quattro`, not through the
normal migration runner. Do not add compatibility migrations for old installer
layouts; put pre-4 package-layout transition work in the upgrade command instead.

Clearing a privileged file that a retired installer left on disk is the exception, and belongs in a migration whether or not that installer was part of a package layout transition. The upgrade command only runs on a machine still making the 3 to 4 crossing, so anything put there never reaches an install that crossed already, and it never runs at all for an installer that was retired on its own — while the file the installer wrote is still sitting on those machines. The upgrade command finishes by running `arch-migrate` (`run_post_upgrade_migrations`), so one migration reaches every population; a copy in the upgrade command would only be a second copy of the same predicate to keep correct. Such a migration must name the defect it clears and match what the old installer actually produced before deleting it. Leave safe administrator-authored files alone; if one still contains the vulnerable privileged action, preserve it under an inactive name rather than discarding custom content or leaving the action executable. A user config that depends on the same retired compatibility path may be repaired in that migration when doing so eliminates an overlapping migration, but only by matching and replacing the exact legacy path while preserving the rest of the file.
