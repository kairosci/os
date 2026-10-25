# Install Scripts

Read this before working under `installer/` or on the system/user setup commands.

The ISO owns installation orchestration. This repo ships target-side setup
commands and reusable setup leaves:

- `src/cli/arch-apply-system` runs root-owned system setup during ISO finalization.
- `src/cli/arch-apply-hardware` runs idempotent hardware-specific setup and is called by `arch-apply-system`.
- `src/cli/arch-finalize-user` runs the per-user runtime finalization (skill symlinks, xdg-user-dirs, mime defaults, `installer/user/all.sh`). Shipped user defaults are seeded by `/etc/skel` from `arch-settings`, not by this command. `src/cli/arch-reinstall-configs` is the explicit destructive resync of those defaults into an existing user's `$HOME`.
- leaf scripts under `installer/` are sourced by `run_logged $ARCH_INSTALL/path/to/script.sh` and intentionally do not have shebangs.
- avoid `exit` in sourced setup scripts unless intentionally aborting setup.
- use `$ARCH_INSTALL` and `$ARCH_PATH` instead of hard-coded Arch paths.
- keep root-scoped hardware setup under `installer/hardware/` and orchestrate it through `installer/hardware/all.sh`.
- in an image build every `run_logged` leaf in `installer/hardware/all.sh` is queued and runs on the machine's first boot instead (`src/cli/arch-provision-hardware`, see `docs/file-layout.md`), possibly offline, using packages already in the image, and before any user exists; keep those leaves idempotent and put nothing but `run_logged` lines in `all.sh`.
- gate platform-specific setup on a predicate built on `arch-hw-platform` (`arch-hw-aarch64-apple`), not on `uname -m`; architecture checks (`arch-hw-x86`, `arch-hw-aarch64`) are only for ABI, binary availability or a repository's `$arch`. Platform names and where platform code lives are in the Platforms section of `AGENTS.md`.
- keep every per-user setup leaf under `installer/user/` (including `installer/user/hardware/` and `installer/user/first-run/`) so it is clear what must run for each user.
- The base install supplies matching kernel headers before hardware setup. DKMS installers should install their driver packages and assume the headers exist.
- prefer helper commands for package and command checks where available.

Raw `command -v`, `pacman`, and `pacman-key` are acceptable in package-helper
contexts where direct package-manager behavior is the point of the script.
