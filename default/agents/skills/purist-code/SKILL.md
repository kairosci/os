# Purist Code

Use this skill for every change to Arch code, configuration, packaging, and documentation. The goal is the smallest complete implementation that follows the project's native interfaces and leaves no unnecessary machinery behind.

## Before editing

- Read the relevant `AGENTS.md`, task guide, owning module, and nearby tests.
- Inspect the current worktree and preserve unrelated user changes.
- Trace the behavior from its public entry point through configuration,
  runtime, migration, and documentation before changing it.
- State the invariant the change must preserve and the failure it must prevent.

## Implementation rules

- Prefer existing project abstractions and authoritative configuration over new constants, duplicated lists, compatibility layers, fallback paths, or one-off helpers.
- Use `AP` as the sole canonical Arch runtime root (`$AP`, `os.environ["AP"]`, or `Quickshell.env("AP")`). Read the previous variable name only in a one-time migration that transfers an existing configuration or session-manager value.
- Put user-adjustable values in the owning configuration format. Keep code responsible for behavior and validation, not duplicating configuration.
- Remove obsolete paths and their callers, tests, documentation, package references, and migration support when the feature is retired.
- Keep one source of truth for each behavior. Do not add a second provider,
  command, tool, or configuration path that duplicates an existing one.
- Use native platform interfaces and repository conventions. Do not invent
  abstractions to hide simple control flow.
- Validate inputs at trust boundaries. Avoid shell evaluation, unsafe temporary files, broad permissions, and implicit privilege escalation.
- Keep changes focused and explainable. Delete dead code instead of leaving
  commented-out alternatives or speculative generalization.
- When an AI authors a pull request, leave its body empty. Do not add generated summaries, checklists, or filler.

## Completion

- Review the full diff for accidental churn, hardcoded policy, dead code, duplicated sources of truth, and generated artifacts that do not belong.
- Run only the focused checks required by the repository instructions.
- For visual changes, follow `.agents/skills/visual-verification.md` and inspect a real screenshot of the running UI.
- Report any requirement that remains incomplete or cannot be verified. Never
  claim that a change has no errors without evidence.
