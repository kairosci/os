# The Arch CLI router

`src/arch/commands/archctl` maps spaced commands onto the flat `src/arch/commands/arch-*` namespace:
`archctl theme set foo` becomes `exec arch-theme-set foo`. There is no
registry to maintain — every executable `src/arch/commands/arch-*` file is a command, and
its filename is its default route. Metadata comments in the file header refine
how it presents and routes; the keys are documented in
[`.agents/skills/command-metadata.md`](../.agents/skills/command-metadata.md).
This document covers what that guide does not: how resolution and dispatch
actually work.

## How a binary becomes routes

The stem after `arch-` splits at the first hyphen: `arch-theme-set` gets group `theme` and name `set`, with remaining hyphens becoming spaces. The Python route `archctl hw laptop` resolves to group `hw` and name `laptop`. A single-segment stem (`arch-update`) is the root command of its own group, with an empty name.

Every command registers two routes: the canonical route `arch <group>
<name>` after metadata overrides, and the filename route with *all* hyphens
turned to spaces. When metadata moves nothing, they are the same route. When it
does, both keep working — `# arch:name=gaming xbox-cloud` on
`arch-install-gaming-xbox-cloud` keeps the hyphen inside the name, so
`archctl install gaming xbox-cloud` is canonical while the filename route
`archctl install gaming xbox cloud` still resolves. An explicitly *empty* `#
arch:name=` makes a command the root of its group: `arch-menu-share` sets
`group=share` and an empty name, so its canonical route is `arch share`
while `archctl menu share` remains as the filename route. Alias routes register
the same way but are flagged, so listings show them as aliases rather than
commands.

Two routes claiming different binaries is a collision: the first registration
wins, dispatch is unaffected, and the conflict is recorded for `archctl
commands --check` to report. Hidden commands (`# arch:hidden=true`) still
register and dispatch normally — hiding only removes them from listings, which
is how install-time plumbing like `arch apply hardware` stays callable
without being browsable.

Metadata is read from the comment header only: the first 80 lines, stopping at
the first non-comment line, so metadata-shaped comments after code never take
effect. Malformed `arch:` lines and unknown keys are ignored rather than
fatal — a typo degrades a command to its filename route instead of breaking the
router. The first plain comment line doubles as a fallback summary, and a
command with no comments at all still gets a generated one, though `--check`
demands the explicit form (below).

## Dispatch

Resolution is longest-prefix: the router tries the full argument list as a
route, then drops trailing words until something matches. Whatever it drops is
passed to the binary as arguments. This runs in two passes.

The fast path joins argument prefixes with hyphens and checks for an
executable file: `archctl theme set foo` probes `arch-theme-set-foo`, then
`arch-theme-set`, which exists — resolved without reading a single metadata
header. This exists because plain dispatch is the hot path: parsing the
headers of several hundred binaries on every invocation is measurable
latency (`arch dev benchmark cli` tracks it), and a filename probe is a few
stat calls. Metadata loads lazily, only for the resolved command when help is
needed.

When no filename matches — metadata-moved routes like `arch share`, and aliases like `archctl screenshot` — the router first loads only the commands that could own a route under the first word: those whose filename starts with it, and those whose header names it as their group or in an alias. If that resolves a route that runs its command, it dispatches from there, about as fast as a filename route. Help output, a route that needs arguments it wasn't given, and anything still unresolved fall back to loading all metadata and resolving against the full route table, with the same longest-prefix rule, since help lists related commands from the whole table.

Both paths intercept `--help`/`-h` *anywhere* in the leftover arguments, not
just the first one. Resolution can succeed with unresolved words still ahead of
the flag — `archctl update aur --help` resolves `update` with leftovers `aur
--help` — and checking only the first leftover once let that invocation start a
real update. A `--` ends the scan: everything after it belongs to the command,
so `arch foo run -- --help` forwards the flag. `--json` alongside `--help`
switches the help output to the command's JSON record; `--json` alone is just
an argument for the command.

Bare invocations are also guarded. If a command declares required arguments
(its `args` metadata, minus `[bracketed]` optional parts, is non-empty) and
none were given, the router shows help instead of executing — `archctl theme
set` prints usage rather than running an interactive setter. A bare group name
with child commands shows the group help.

Dispatch is `exec`: the router process is replaced, the binary sees only the
leftover arguments, and the exit code is the binary's own. The router itself
exits 127 for unknown routes or missing binaries.

When nothing resolves, the router tries a prefix listing — `arch hw asus`
prints every command whose usage starts with that prefix — and otherwise
errors with a "did you mean" suggestion (a known route extending the first
word) and a pointer to `archctl commands --all`.

## Groups and the top-level listing

Group help is synthesized from metadata, not written anywhere. A command
belongs to a group when either its metadata group or its filename group
matches, listed under the route that fits the group being viewed: `archctl
menu --help` shows `arch-menu-share` as `archctl menu share`, while its
canonical `arch share` stands alone. On the fast path, group help loads
only that group's filename-prefixed binaries rather than everything.

The top-level `arch` listing is driven entirely by the hand-curated
`GROUP_DESCRIPTIONS` table in `src/arch/commands/archctl`, which also titles each group's
help. An entry there advertises the group even when every command in it is
hidden — which is exactly why `apply` and `provision` have none: they route,
but a listing entry would put install-time plumbing back in front of users
(see the Command Naming section of `AGENTS.md`). Adding a browsable command
group means adding its `GROUP_DESCRIPTIONS` entry; adding hidden plumbing
means deliberately not doing so.

## Introspection

`archctl commands` prints every non-hidden command with its summary, plus an
alias table. `--all` includes hidden commands, `--markdown` emits a table, and
`--json` emits full records: route, binary, group, name, summary, flags, args,
examples, aliases, `filename_route`, and `routes` (the union of everything
that resolves to the binary). Per-command JSON comes from `arch <route>
--help --json`.

`archctl commands --check` is the metadata lint, run by `tests/cli`. It fails
on:

- route collisions between binaries
- a missing explicit `# arch:summary=` — a plain-comment fallback renders
  in help but does not satisfy the check
- invalid boolean metadata: `hidden` and `requires-sudo` must be `true` or
  omitted, never `false`
- a registered command whose binary is missing or not executable

When debugging a routing surprise, `arch <route> --help` shows the resolved
binary and, when it differs, the filename route; `archctl commands --all
--json` shows every route the router knows.
