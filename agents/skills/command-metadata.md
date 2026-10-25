# Command Metadata

Read this before adding or changing commands in `src/cli/`.

Commands in `src/cli/` can declare CLI metadata in comments near the top of the
file. `src/cli/archctl` scans the first 80 lines, and tests expect command metadata
to remain valid.

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
