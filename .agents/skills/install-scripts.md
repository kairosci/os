# Install Scripts

Read this before working under `installer/` or on the system/user setup commands.

The ISO owns installation orchestration. This repo ships target-side setup
commands and reusable setup leaves:

- `src/commands/os-apply-system` runs root-owned system setup during ISO finalization.
- `src/commands/os-apply-hardware` runs idempotent hardware-specific setup and is called by `os-apply-system`.
- `src/commands/os-provision-user` runs the per-user runtime finalization (skill links, xdg-user-dirs, MIME defaults, `src/python/installer_user/all.py`). Shipped user defaults are seeded by `/etc/skel` from `arch-settings`, not by this command. `src/commands/os-reinstall-configs` is the explicit destructive resync of those defaults into an existing user's `$HOME`.
- Python setup leaves under `src/python/installer/` run in isolated Python. Remaining shell leaves under `installer/` are sourced by `src/python/installer/run_logged.py $ARCH_INSTALL/path/to/script.sh` and intentionally do not have shebangs.
- avoid `exit` in sourced setup scripts unless intentionally aborting setup.
- use `$ARCH_INSTALL` and `$ARCH_PATH` instead of hard-coded Arch paths.
- keep root-scoped hardware setup under `src/python/installer/hardware/` and orchestrate it through `src/python/installer/hardware/all.py`.
- in an image build every leaf declared by `src/python/installer/hardware/all.py` is queued and runs on the machine's first boot instead (`src/commands/os-provision-hardware`, see `docs/file-layout.md`), possibly offline, using packages already in the image, and before any user exists; keep those leaves idempotent and keep the declared order explicit.
- gate platform-specific setup on a predicate built on `os-hw-platform` (`os-hw-aarch64-apple`), not on `uname -m`; architecture checks (`os-hw-x86`, `os-hw-aarch64`) are only for ABI, binary availability or a repository's `$arch`. Platform names and where platform code lives are in the Platforms section of `AGENTS.md`.
- keep every per-user setup leaf under `src/python/installer_user/` (including `hardware/` and `first_run/`) so it is clear what must run for each user.
- The base install supplies matching kernel headers before hardware setup. DKMS installers should install their driver packages and assume the headers exist.
- prefer helper commands for package and command checks where available.

Raw `command -v`, `pacman`, and `pacman-key` are acceptable in package-helper
contexts where direct package-manager behavior is the point of the script.
