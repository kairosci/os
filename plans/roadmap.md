# Repository consolidation roadmap

This roadmap tracks the requested CLI, ISO, desktop, and release work as separate reviewable sprints. The goal is a single checkout that contains the complete build and release path, Python modules behind the unified CLI, and a desktop with scrolling as its default layout and tiling as its only alternative.

## Current evidence

- Release asset tooling is integrated in `scripts/iso/`; it splits images below GitHub's asset limit, verifies checksums, and downloads and assembles release parts.
- `make iso` still calls a sibling ISO builder and package checkout. The repository has package lists and runtime package sources, but does not yet have the bootable profile or live installer program.
- The CLI catalog already maps many routes to Python modules. Compatibility entrypoints and shell command implementations remain under `src/cli/os-*`, and code still calls those names directly.
- The desktop layout implementation is being converted to the public modes `scrolling` and `tiling`; the compositor's internal layout names remain an implementation detail.

## Sprints

### 1. Finish the public layout contract

Make `scrolling` the default in every shipped configuration, expose only `scrolling` and `tiling` in commands and menus, and migrate stored preferences without losing existing workspace state. Update English and Italian documentation and catalogs together. Verify the setting, current-mode query, toggle, and migration with focused tests.

### 2. Inventory and classify CLI entrypoints

For each executable in `src/cli/os-*`, record whether it is a Python compatibility wrapper, a shell implementation, or a caller-facing executable that still has references elsewhere in the repository. Match every public route to its catalog record and Python module. Keep the inventory generated from the catalog so it cannot silently drift.

### 3. Move remaining command behavior into modules

Port each shell implementation into a feature module under `src/cli/`, retaining the existing command arguments, exit statuses, privilege boundary, and user-visible output. Add or extend focused tests for behavior with real logic. Update in-repository callers to use `os <group> <command>` and add regression coverage for routes whose argument forwarding differs from the old executable form.

### 4. Remove flat compatibility entrypoints

After all commands are catalogued, implemented as Python modules, and all in-repository callers use the unified router, remove `src/cli/os-*` compatibility files and the router's executable-discovery fallback. Keep only the `os` entrypoint. Update package assembly, command metadata checks, docs, and tests in the same sprint; verify that every catalog route imports a real module and that command groups and help still work.

### 5. Bring package build inputs into this repository

Make the package set reproducible from this checkout. Build the runtime and settings packages from their local `PKGBUILD`s, describe third-party package sources and versions in repository-owned manifests, and fail before ISO work starts when a source or package is unavailable. Keep architecture-specific packages explicit and preserve the platform names defined in `AGENTS.md`.

### 6. Add the local ISO profile and builder

Replace sibling-checkout assumptions in `Makefile` with a repository-owned builder under `scripts/iso/` and a checked-in profile. The builder should validate its host tools and target, build or fetch every declared package source, create the local package repository, invoke ArchISO, and emit a checksum manifest. `make iso` should work from a fresh checkout with documented host dependencies and no implicit paths outside the repository.

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
