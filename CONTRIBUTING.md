# Contributing

## Branch and pull request flow

Create a branch from `main` for one module or one shared module contract. Use `feat/<module>/<change>`, `fix/<module>/<change>`, or `refactor/<module>/<change>` names. Use Conventional Commits for commit messages, with the module ID as the scope when it is known.

Open a pull request against `main`. Keep the change within its declared module boundary, update dependent modules in the same change when their contract requires it, and include behavior evidence and the exact checks run. Changes to installed configuration also update the home setup path; changes to package contents also update the package manifest and package verification.

The required review checks are the module graph, source formatting and syntax checks for changed languages, focused module tests, and integration checks for declared dependents. Boot, login, disk encryption, and package transaction changes also require review of the generated artifacts and their install order.

## Module ownership

Every module declares one owner domain and its public inputs and outputs in `module.toml`. A module may depend on another module through its ID and declared interface. It may not read another module's private source files directly. Shared behavior belongs in a named shared module and is consumed through that module's public interface.

Third-party code with an independent release process may be tracked as a Git submodule. First-party components share the main repository and are nested under `modules/<domain>/<capability>/<component>`.

## Configuration and package changes

User settings belong under `~/.config/arch`; generated runtime state belongs under `~/.local/state/arch`. System configuration is installed by packages and setup commands. A developer checkout is not a runtime dependency. Package changes keep source ownership, installed destinations, file permissions, and removal behavior explicit.

## Local checks and ISO builds

Install the repository's developer tools with `mise install`. Run `make check` for source syntax, module ownership, CLI, and shell checks. Use `make type-check` to run the strict type checker on the module catalog validator, and `make lint-workflows` to validate GitHub Actions and their embedded shell. `make security-scan` runs Trivy against dependency manifests, configuration, and secrets.

Build an ArchISO profile with `make iso ISO_PROFILE=path/to/profile`. The image is written under `build/iso`; set `ISO_OUTPUT` and `ISO_WORK` to choose different output and work directories.
