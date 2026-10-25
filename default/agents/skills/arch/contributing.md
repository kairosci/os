# Reporting Issues and Submitting PRs

Read this when the user wants to report an os bug, suggest a feature, or
contribute a fix upstream.

os lives at https://github.com/kairosci/arch Route requests to the
right place:

- **Verified bugs** -> GitHub issues. Issues are for validated bugs only, not
  support requests.
- **Feature ideas and suggestions** ->
  https://github.com/kairosci/arch
- **Support and "is this a bug?" questions** -> the Discord community at
  https://github.com/kairosci/arch/discord. Start here when the problem isn't clearly a bug
  in os itself.

## Filing a Good Bug Report

The bug template asks for system details (CPU, GPU, os version), a
description with steps to reproduce, and diagnostics. Gather them:

```bash
archctl version

# Generate the diagnostic log (also written to /tmp/arch-debug.log)
archctl debug --no-sudo --print

# Interactive variant: `archctl debug` offers to upload the log to
# logs.github.com/kairosci/arch (expires after 24h) and prints a shareable URL to
# include in the issue.
```

**Capture the problem on screen.** A screenshot or short recording of the bug
is often worth more than the description — see [`capture.md`](capture.md) for
`archctl capture screenshot` and `arch screenrecord`. Keep recordings short
and focused on the misbehavior. GitHub issue attachments are added by
drag-and-drop in the web form, so save the capture and hand the user the file
path to attach (`gh` cannot upload media).

For screen-recording failures specifically, rerun with
`ARCH_SCREENRECORD_DEBUG=true` and attach `$XDG_RUNTIME_DIR/arch-screenrecord.log` (or `${XDG_STATE_HOME:-$HOME/.local/state}/arch/arch-screenrecord.log` without a session runtime directory).

File the issue with `gh` when available:

```bash
gh issue create --repo omacom/arch --title "..." --body "..."
```

Include: what happened, what was expected, steps to reproduce, system details,
the debug log URL (or attached log), and the capture.

## Submitting a PR

Never develop against `/usr/share/arch`. Clone a working copy instead:

```bash
gh repo fork omacom/arch --clone
cd arch
```

Follow the repository's own `AGENTS.md` for style, testing, and commit
conventions — it is the authority on contributions. Keep commits atomic, run
`./tests/all` before pushing, and open the PR with `gh pr create`. A PR that
fixes a visual problem should include before/after captures (again, see
[`capture.md`](capture.md)).
