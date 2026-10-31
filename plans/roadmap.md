# Repository consolidation roadmap

This roadmap tracks the requested CLI, ISO, desktop, and release work as separate reviewable sprints. The goal is a single checkout that contains the complete build and release path, Python modules behind the unified CLI, and a desktop with scrolling as its default layout and tiling as its only alternative.

## Current evidence

- `scripts/iso/` contains the CI-only native builder, checksum manifest, downloader, assembler, and release publisher. Workflow run `41202718530` built both x86_64 and AArch64 images successfully; publishing was skipped. The complete image artifacts were about 1.82 GB and 1.74 GB, and each release-assets artifact contained three files, corresponding to two image parts plus a manifest with the configured 1,000,000,000-byte cap. No GitHub release has been published, so download and assembly from a published release remain unverified.
- `scripts/iso/profile/profiledef.py` is the checked-in Python profile renderer and reads `data/iso/profile.yml`; the CI builder emits ArchISO's required `profiledef.sh` only inside its temporary staging profile. The builder creates a complete ISO and release parts capped at 1,000,000,000 bytes each, below GitHub's 2 GB per-asset limit. `scripts/iso/download.py` verifies release metadata and delegates checksum-checked assembly to `scripts/iso/parts.py`. The ISO includes `archinstall`, but this build evidence does not prove the repository's intended online, offline, and unattended target-install flows; those remain open for disposable-VM acceptance.
- After PR #583, `src/arch/commands/` contains 374 command files and `src/arch/cli/` contains 56 Python modules. Eighty entrypoints are declared in `data/cli/python-entrypoints.yml`; PRs #538, #541, #545, #547, #548, #549, #550, #551, #552, #553, #556, #557, #558, #559, #561, #562, #563, #564, #565, #566, #567, #568, #569, #570, #571, #573, #574, #575, #577, #578, #579, #580, #581, #582, and #583 removed their matching source wrappers and generate package launchers from YAML. The remaining flat commands still need classification and migration before the requested cleanup is complete.
- PR #507 established `scrolling` as the default and `tiling` as the only alternate public workspace mode. Stored legacy layout values are normalized during configuration loading; the compositor's internal layout names are implementation details.
- PRs #542 and #555 keep every shipped window and layer rule, including global tiling and transparency defaults, in the user-editable `config/hypr/apps.yml`. Disktree tiles and maximizes into the active display's usable area instead of using a fixed pixel size. The YAML loader reports an invalid user file and applies packaged defaults so a typo does not disable the desktop's window rules. The menu overflow indicator and the event-driven battery glyph refresh have been integrated; the current charging glyph has not been visually checked on a machine connected to external power.
- The theme asset tree contains no keyboard image asset or keyboard-image reference. PR #539 removed Windows VM install and removal rows from the default menu; the existing command and user data remain untouched. Menu hierarchy, labels, focus behavior, and visual verification still need a broader review.
- PR #584 replaces the full-screen black startup cover and the wallpaper layer’s transparent clear surface with the active theme background color. The shell service is already continuously supervised by systemd and by its launcher (PR #560). The code path removes two causes of an all-black desktop, but live visual verification still needs an isolated graphical VM; it has not been run because the available checkout has no sibling `arch-iso` harness and the active desktop must not be interrupted.
- PR #585 moves the clipboard and emoji menu launchers into `src/arch/cli/menu/launch.py`, with their exact `arch-shell` argv, timeout, statuses, and messages in YAML. With PR #585 integrated, the repository has 372 flat command files, 57 Python modules, and 82 Python entrypoints. Their existing binary names stay available through generated launchers for installed menu actions and user scripts.
- PR #586 moves both Files launchers into Python, keeping application argv and the terminal-directory helper in YAML. PR #587 generalizes that module to `src/arch/cli/launch/dispatch.py` and migrates the tmux terminal launcher with its exact attach-or-create command in YAML. With PR #587 integrated, the repository has 369 flat command files, 58 Python modules, and 85 Python entrypoints.
- PR #588 migrates emoji insertion into `src/arch/cli/menu/emoji_insert.py`. Clipboard and paste argv, timing, limits, statuses, and messages are YAML data; the clipboard provider runs in a dedicated process group and is terminated on every exit path. With PR #588 integrated, the repository has 368 flat command files, 59 Python modules, and 86 Python entrypoints.
- The Arch shell user service starts from Hyprland autostart, remains under `Restart=always`, and its launcher retries Quickshell exits. PR #589 gives Hyprland a non-black clear color beneath the shell wallpaper so a missing layer does not clear to pure black; verify the recovery appearance in a disposable graphical session before closing the blank-desktop sprint.

## Sprints

### 1. Finish the public layout contract — integrated

PR #507 made `scrolling` the default and exposed `tiling` as the only alternate public mode. Its configuration migration preserves existing workspace state and maps prior stored values to the supported modes. Keep this contract intact as CLI commands and menus are refined.

### 2. Inventory and classify CLI entrypoints

For each executable in `src/arch/commands/`, record whether it is already backed by a Python module, still contains command behavior, or has callers that rely on its binary name. Eighty-six Python entrypoints are catalogued after PR #588, but the remaining 368 command files have not been classified. Keep the inventory generated from source metadata so it cannot silently drift.

### 3. Move remaining command behavior into modules

Port each remaining command implementation into a feature module under `src/arch/cli/`, retaining its arguments, exit statuses, privilege boundary, and user-visible output. Update in-repository callers to use `os <group> <command>` and account for routes whose argument forwarding differs from the old executable form.

### 4. Remove flat compatibility entrypoints

After commands are catalogued, implemented as Python modules, and all in-repository callers use the unified router, remove their flat compatibility files and executable-discovery fallbacks. Keep only the `os` entrypoint. Update package assembly, command metadata, and documentation in the same sprint; verify that every catalog route imports a real module and that groups and help still work.

### 5. Bring package build inputs into this repository

Make the package set reproducible from this checkout. Build the runtime and settings packages from their local `PKGBUILD`s, describe third-party package sources and versions in repository-owned manifests, and fail before ISO work starts when a source or package is unavailable. Keep architecture-specific packages explicit and preserve the platform names defined in `AGENTS.md`.

### 6. Add the ISO profile and CI-only builder — implemented, acceptance open

The repository-owned builder lives under `scripts/iso/`, and its profile values are rendered from YAML by `profiledef.py`. It validates tools and targets, builds the local package repository, invokes ArchISO only in the dedicated GitHub Actions workflow, and emits checksum-verified parts capped at 1,000,000,000 bytes. Local commands download and assemble images but cannot generate them. Run `41202718530` passed native builds on both supported runner architectures; its release-assets artifacts contained two parts and a manifest per image under the new cap. Publishing and download/assembly from an actual release, plus boot and installation acceptance, remain open.

### 7. Port the live installer and unattended path

Bring the actual installation UI and its target provisioning code into repository-owned modules before calling the image complete. Preserve the supported full-disk and free-space flows, encryption defaults, user setup, platform dispatch, regional defaults, and unattended configuration. Make the live environment boot to the installer and keep the ordinary desktop runtime out of the installed target until provisioning requests it.

### 8. Connect release assembly and distribution

Have the release workflow build the ISO from the local profile, validate the resulting image, split it into assets no larger than 2 GB, publish the manifest, and attach all parts to the release. Keep the existing downloader's checksum checks and atomic reassembly. Test failure paths for missing, oversized, and corrupted assets.

### 9. Move default app rules into user configuration — implemented

PR #542 moved all default window and layer behavior for shipped applications into `config/hypr/apps.yml`, which is copied into new user profiles and can be restored for existing profiles with `archctl refresh config hypr/apps.yml`. The loader treats YAML as data, bounds its size and nesting, and uses packaged defaults with a diagnostic when a user's file is invalid. PR #555 keeps Disktree in the active tiled layout area. Verify the running UI when the package is rolled out.

### 10. Finish menu and theme polish — in progress

The requested keyboard image is absent from the current theme assets and references. PR #539 removed Windows VM install and removal rows from the default menu and pruned their English and Italian catalog entries. Review the remaining hierarchy, labels, duplicate routes, checked state, keyboard navigation, and per-application defaults against the supported layout modes, then verify visible changes in the running desktop.

### 11. Release acceptance

Build each supported image target from a clean checkout, boot it in a disposable VM where applicable, complete an online and offline install, and exercise the unattended path. Download a published multipart asset set and verify that the assembled ISO matches the build checksum. Close the roadmap only after the actual build, boot, install, and release artifacts pass these gates.

## Completion rule

A sprint is complete only when its implementation, caller updates, docs, and focused verification are in the same reviewable change. The ISO objective is complete only when the repository-owned builder produces the installable image and the release workflow publishes verified parts; release-part helpers alone do not satisfy that requirement.

### 12. Prevent blank desktop surfaces — in progress

PR #584 gives the wallpaper layer an opaque theme-colored fallback and removes the intentional black startup cover. PR #589 sets Hyprland's compositor clear color to a visible dark gray, and the shell process remains under the existing systemd restart policy and launcher supervisor. Verify the missing-wallpaper and shell-recovery states in a disposable graphical VM before closing this sprint; never restart the active desktop to perform that check.

### 13. Move menu launch behavior into modules — implemented

PR #585 migrates the clipboard and emoji toggle launchers into one Python module; PR #588 migrates emoji insertion with a bounded UTF-8 input and cleanup of the transient clipboard process group. Command arrays, timing, limits, and failure output are YAML data, while generated entrypoints preserve the names used by the menu.

### 14. Migrate launch commands — implemented

PRs #586 and #587 move the Files and tmux terminal launch commands into `src/arch/cli/launch/dispatch.py`, preserving generated binary names. The terminal directory comes from the existing helper with a configured timeout and remains one argument when it contains spaces. The tmux attach-or-create command is declared in YAML.

### 15. Migrate the terminal tmux launcher — implemented

PR #587 moves the remaining `arch-launch-terminal-tmux` wrapper into the shared launch dispatcher. Its full argv, including the tmux attach-or-create expression, is YAML data; the Python module selects by generated entrypoint name and replaces itself with the configured launcher.

### 16. Migrate emoji insertion — implemented

PR #588 moves emoji insertion into a Python module. The clipboard provider is started in its own process group, receives bounded UTF-8 input, remains available through Shift+Insert, and is stopped in `finally` with a bounded TERM/KILL cleanup. The focused emoji test, strict Python type check, CLI contract suite, and menu package assembly passed before integration.
