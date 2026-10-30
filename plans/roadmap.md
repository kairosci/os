# Repository consolidation roadmap

This roadmap tracks the requested CLI, ISO, desktop, and release work as separate reviewable sprints. The goal is a single checkout that contains the complete build and release path, Python modules behind the unified CLI, and a desktop with scrolling as its default layout and tiling as its only alternative.

## Current evidence

- `scripts/iso/` contains the CI-only native builder, checksum manifest, downloader, assembler, and release publisher. The x86 build produced a complete ISO in CI; the AArch64 builder now uses a pinned, signature-verified ARMv8 repository, and its post-merge build is still running. No release has been published because validation runs use `publish=false`.
- The ISO profile is rendered from `data/iso/profile.yml`, and local runtime packages are built from this checkout. The full installer and its target provisioning flow are still absent from the ISO; end-to-end boot and install acceptance remains open.
- The current source tree has 28 Python CLI modules and 454 flat command files under `src/arch/commands`; only four Python entrypoints are generated from `data/cli/python-entrypoints.yml`. The requested unified `os` router and removal of migrated flat wrappers are not complete. Build a generated route inventory before continuing module migration so callers and package assembly stay accounted for.
- The workspace default is `scrolling`, and the menu presents `scrolling` and `tiling`. Stored legacy values are normalized at load, while compositor layout names remain implementation details.
- Disktree has a shipped per-application Hyprland rule in `default/hypr/apps/disktree.lua`. The menu overflow indicator and battery glyph refresh have also been integrated; visual verification of the current battery charge state still needs a machine connected to external power.

## Sprints

### 1. Finish the public layout contract

Make `scrolling` the default in every shipped configuration, expose only `scrolling` and `tiling` in commands and menus, and migrate stored preferences without losing existing workspace state. Update English and Italian documentation and catalogs together. Verify the setting, current-mode query, toggle, and migration with focused tests.

### 2. Inventory and classify CLI entrypoints

For each executable in `src/arch/commands/`, record whether it is already backed by a Python module, still contains command behavior, or has callers that rely on its binary name. Match every public route to its YAML metadata and Python module. Keep the inventory generated from the catalog so it cannot silently drift.

### 3. Move remaining command behavior into modules

Port each remaining command implementation into a feature module under `src/arch/cli/`, retaining its arguments, exit statuses, privilege boundary, and user-visible output. Update in-repository callers to use `os <group> <command>` and account for routes whose argument forwarding differs from the old executable form.

### 4. Remove flat compatibility entrypoints

After commands are catalogued, implemented as Python modules, and all in-repository callers use the unified router, remove their flat compatibility files and executable-discovery fallbacks. Keep only the `os` entrypoint. Update package assembly, command metadata, and documentation in the same sprint; verify that every catalog route imports a real module and that groups and help still work.

### 5. Bring package build inputs into this repository

Make the package set reproducible from this checkout. Build the runtime and settings packages from their local `PKGBUILD`s, describe third-party package sources and versions in repository-owned manifests, and fail before ISO work starts when a source or package is unavailable. Keep architecture-specific packages explicit and preserve the platform names defined in `AGENTS.md`.

### 6. Add the ISO profile and CI-only builder

Keep the repository-owned builder under `scripts/iso/` and its profile values in YAML rendered by `profiledef.py`. Validate host tools and build targets, produce the local package repository, invoke ArchISO only in the dedicated GitHub Actions release workflow, and emit bounded release parts with a checksum manifest. Local commands may download and assemble published images but must not generate an ISO. Completion requires successful native builds on both supported runner architectures.

### 7. Port the live installer and unattended path

Bring the actual installation UI and its target provisioning code into repository-owned modules before calling the image complete. Preserve the supported full-disk and free-space flows, encryption defaults, user setup, platform dispatch, regional defaults, and unattended configuration. Make the live environment boot to the installer and keep the ordinary desktop runtime out of the installed target until provisioning requests it.

### 8. Connect release assembly and distribution

Have the release workflow build the ISO from the local profile, validate the resulting image, split it into assets no larger than 2 GB, publish the manifest, and attach all parts to the release. Keep the existing downloader's checksum checks and atomic reassembly. Test failure paths for missing, oversized, and corrupted assets.

### 9. Finish menu and theme polish

Remove the keyboard image from every theme variant and its references. Review the menu hierarchy, labels, duplicate routes, checked state, and keyboard navigation against the supported layout modes. Keep the English and Italian catalogs synchronized and verify visible changes in the running desktop.

### 10. Release acceptance

Build each supported image target from a clean checkout, boot it in a disposable VM where applicable, complete an online and offline install, and exercise the unattended path. Download a published multipart asset set and verify that the assembled ISO matches the build checksum. Close the roadmap only after the actual build, boot, install, and release artifacts pass these gates.

## Completion rule

A sprint is complete only when its implementation, caller updates, docs, and focused verification are in the same reviewable change. The ISO objective is complete only when the repository-owned builder produces the installable image and the release workflow publishes verified parts; release-part helpers alone do not satisfy that requirement.
