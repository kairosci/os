# Repository architecture target

## Source of truth

This repository is the source for Arch's packages. A running installation uses package-owned files under `/usr/share/arch` and user-owned settings under `~/.config/arch`; it never loads code from a developer checkout. Package builds assemble module sources into the installed layout.

## Target layout

```text
assets/
  applications/
  branding/
  themes/cosmic/
config/
  system/
  user/
  platforms/<architecture>/<platform>/
docs/
  architecture/
  user/
installer/
  boot/
  hardware/<architecture>/<platform>/
  login/
  post-install/
  provisioning/
  user/
migrations/
modules/
  desktop/<capability>/<component>/
  system/<capability>/<component>/
  development/<capability>/<component>/
  module.toml
packages/<package-name>/
src/
  cli/<capability>/<command>/
  shell/
    Commons/
    Ui/
    services/
    plugins/<plugin>/
tests/
  unit/
  integration/
  acceptance/
```

The directory groups have distinct owners: `src` contains executable source, `modules` declares component boundaries and dependencies, `config` contains shipped configuration, `assets` contains non-executable data, `installer` provisions a machine, `migrations` changes an existing installation, `packages` builds pacman packages, `tests` verifies behavior, and `docs` explains the architecture and the installed system.

## Module contract

Each module in the target layout has one `module.toml` declaring its stable ID, owning domain, dependencies, source roots, installed destinations, package owner, and verification commands. Dependencies form an acyclic directed graph. The module assembler validates that graph and rejects two modules that claim the same installed destination. It emits the package tree used by PKGBUILDs; runtime paths remain package-owned and are not derived from the checkout. A manifest is added with its real component, source, and verification in the same change.

Nested capabilities live below their domain, and independently installable components live one level below the capability. A shell plugin is a module; its manifest, QML, and focused tests stay together. Hardware-specific behavior is a platform module selected by architecture and detected hardware. Shared user configuration is owned by the config module and installed into the user's home by the setup commands.

Git submodules are reserved for separately released components with their own maintainers and release cadence. Components developed and released together stay in this repository as nested modules so one change can update source, configuration, migrations, packaging, and verification in one reviewed change.

## Migration map

| Current source | Target owner |
| --- | --- |
| `bin/` | `src/cli/<capability>/<command>/` |
| `src/shell/plugins/<plugin>/` | `src/shell/plugins/<plugin>/` |
| `src/shell/Commons/`, `Ui/`, `services/`, `shell.qml` | `src/shell/` shared runtime |
| `default/` | `config/system/` and the owning `modules/` component |
| `config/` | `config/user/` |
| `applications/` | `assets/applications/` |
| `themes/` | `assets/themes/` |
| `install/` | `installer/` |
| `migrations/` | `migrations/`, grouped by owning system module |
| `test/` | `tests/` |
| `manual/` | `docs/user/` |
| `packaging/` | `packages/` |

The installed tree is assembled from these source owners. Renames update the assembler, package manifests, documentation, and tests in the same pull request; no source-tree symlink layer is part of the layout.

## Pull request units

The migration is reviewed in dependency order. A pull request owns one module boundary or one cross-module contract, updates its consumers, and includes the verification for that boundary. The initial units are the module graph and assembler, CLI groups, shared shell runtime, each first-party shell plugin, system configuration groups, platform modules, installation stages, migrations, package builds, and user documentation. The 16 shell plugins and 222 existing migrations provide independently reviewable units; command and platform groups are split along their actual ownership boundaries. This is an incremental migration, with each pull request leaving the installable package tree complete.

The rebuilt repository starts with a protected `main`. Work lands through short-lived branches and pull requests. Direct pushes to `main` are disabled; required checks cover the changed module and its declared dependents.
