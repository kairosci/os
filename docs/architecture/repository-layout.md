# Repository architecture

## Source of truth

This repository is the source for Arch's packages. A running installation uses package-owned files under `/usr/share/arch` and user-owned settings under `~/.config/arch`; it never loads code from a developer checkout. Package builds assemble module sources into the installed layout.

## Repository layout

```text
assets/
  applications/
  branding/
  themes/cosmic/
config/
  <application-configurations>/
default/
  <system-and-application-defaults>/
docs/
  architecture/
  user/
etc/
  <system-configuration-subsystems>/
installer/
  boot/
  config/
  hardware/
  helpers/
  login/
  post-install/
  provisioning/
  user/
migrations/
modules/
  desktop/
    commands/<capability>/module.toml
    shell/<plugin>/module.toml
    runtime/module.toml
  system/
    installation/<stage>/module.toml
    settings/defaults/<component>/module.toml
    settings/system-files/<subsystem>/module.toml
    runtime-data/libalpm-hooks/module.toml
packages/
  arch/
  arch-settings/
scripts/
src/
  cli/<command>
  shell/
    Commons/
    Ui/
    services/
    plugins/<plugin>/
tests/
  acceptance.d/
  shell.d/
```

`config/` contains user-facing configuration trees. `default/` contains packaged defaults and templates; `etc/` contains system configuration sources. `assets/` holds non-executable media. `src/` contains runtime code, `installer/` provisions a machine, `migrations/` upgrades an existing installation, `modules/` declares package ownership and dependencies, `packages/` builds pacman packages, and `tests/` verifies behavior.

## Module contract

Each module has one `module.toml` declaring its stable ID, owning domain, dependencies, source roots, installed destinations, and package owner. The module ID and domain must match its directory, and its package must match a PKGBUILD in `packages/`. Dependencies form an acyclic directed graph. The module assembler rejects source symlinks that escape the repository, package output path overlaps, and duplicate destinations across packages. It emits the package tree used by PKGBUILDs; runtime paths remain package-owned. Application settings under `config/` each have an independent module owner, as do the top-level default trees and `/etc` subsystems. Module changes include focused verification in the same change.

Capabilities live below their domain, with independent settings groups below the capability. Each shell plugin has a module, and installer phases, CLI groups, default trees, and `/etc` subsystems have separate module ownership. Hardware-specific scripts remain under `installer/hardware/` and are selected by the hardware provisioning flow.

Git submodules are reserved for separately released components with their own maintainers and release cadence. Components developed and released together stay in this repository as nested modules so one change can update source, configuration, migrations, packaging, and verification in one reviewed change.

## Migration map

| Legacy source | Current owner |
| --- | --- |
| `bin/` | `src/arch/commands/`, with command capability ownership declared under `modules/desktop/commands/` |
| `src/arch/shell/plugins/<plugin>/` | `src/arch/shell/plugins/<plugin>/` |
| `src/arch/shell/Commons/`, `Ui/`, `services/`, `shell.qml` | `src/arch/shell/` shared runtime |
| `default/` | `default/` and `modules/system/settings/defaults/` |
| `etc/` | `etc/` and `modules/system/settings/system-files/` |
| `config/` | `config/` and `modules/system/settings/` |
| `applications/` | `assets/applications/` |
| `themes/` | `assets/themes/` |
| repository-root logos and icons | `assets/branding/` |
| `install/` | `installer/` |
| `migrations/` | `migrations/`, owned by `modules/system/migrations/` |
| `test/` | `tests/` |
| `manual/` | `docs/user/` |
| `packaging/` | `packages/` |

CLI entry points stay together in `src/arch/commands/` because their executable names and sibling helper paths are part of the runtime interface. The module graph groups their ownership by capability without moving those files into nested PATH directories. The installed tree is assembled from source owners. Renames update the assembler, package manifests, documentation, and tests in the same pull request; no source-tree symlink layer is part of the layout.

## Pull request units

The remaining product work is reviewed in dependency order. A pull request owns one module boundary or one cross-module contract, updates its consumers, and includes verification for that boundary. Shell plugins, installer phases, settings, applications, branding, and CLI capabilities already have independent module ownership. Migrations and platform-specific behavior remain reviewable by subsystem. Each change keeps the installable package tree complete.

The rebuilt repository starts with a protected `main`. Work lands through short-lived branches and pull requests. Direct pushes to `main` are disabled; required checks cover the changed module and its declared dependents.
