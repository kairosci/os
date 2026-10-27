# Package-owned state

Use this guide when changing defaults, system configuration, or files under a user's home directory.

## Update model

Pacman packages own installed system files. Declare package contents through `modules/` and ship system defaults with the package that uses them. Let pacman replace package-owned files during upgrades and use its `.pacnew` handling when a local administrator has edited a protected configuration.

Files under a user's home directory remain user-owned. A package upgrade must not rewrite or remove them automatically. Keep runtime readers compatible with existing user configuration when changing its schema. When a user wants the current default, direct them to `archctl refresh config <path>`; this command creates a backup before replacing the file. Interactive setup commands may update user state only after the user asks them to.

Package dependencies and `replaces` metadata express package transitions. Do not add timestamped per-user scripts or update-time code that edits files in a home directory. If a retired package left behind a package-owned system file, remove it through normal package ownership or a narrowly scoped Arch package hook that acts only on that package's files.

First-run provisioning is for new accounts and new installations. It is not a channel for replaying changes against existing user accounts during upgrades.

## Config placement

- `default/` contains packaged defaults and templates.
- `config/` contains user configuration sources copied by `archctl refresh config`.
- `etc/` contains package-owned system configuration sources.
- `data/installer/` contains declarative first-run setup values.
- `modules/` declares which package owns each installed source and destination.

Keep values in the existing YAML data files where a feature already has a YAML schema. Do not add another state database or a second configuration format for a setting already represented by package configuration.
