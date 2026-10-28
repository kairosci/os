# Command Metadata

Read this before adding or changing CLI functionality.

New CLI functionality belongs in the Python package under `src/arch/cli/`; user-visible
values and entrypoint mappings belong in `data/cli/`. Do not add executable files to
`src/arch/cli/`. Python entrypoints listed in `data/cli/python-entrypoints.yml` are emitted
by `scripts/cli_entrypoints.py` during package construction. Existing commands are
being migrated from `src/arch/commands/`; their metadata comments are consumed by the
router and must remain valid while those commands are still there.

The compatibility router in `src/arch/commands/archctl` scans the first 80 lines of
legacy command files, and tests expect their metadata to remain valid.

Supported metadata keys:

- `# arch:group=...` - override the command group inferred from the filename
- `# arch:name=...` - override the command name inferred from the filename
- `# arch:summary=...` - short help text
- `# arch:args=...` - usage arguments
- `# arch:examples=...` - examples separated with ` | `
- `# arch:alias=...` / `# arch:aliases=...` - alternate routes
- `# arch:hidden=true` - hide from default command listings
- `# arch:requires-sudo=true` - mark commands that require sudo

Only use `arch:examples` where there are args that need explaining.

Prefer explicit metadata for user-facing commands. Keep routes consistent with
the filename unless there is a deliberate alias or compatibility route.

Example:

```bash
# arch:summary=Take a screenshot
# arch:args=[smart|region|windows|fullscreen] [slurp|copy]
# arch:examples=archctl screenshot | archctl capture screenshot region
```
