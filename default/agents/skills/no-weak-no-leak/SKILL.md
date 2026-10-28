# No Weakness, No Leak

Use this skill for security-sensitive code, privilege rules, secrets, diagnostics, logging, temporary files, process boundaries, and data collection. Treat every boundary as hostile until the code proves otherwise.

## Security review

- Identify the caller, privilege level, input source, filesystem boundary, process boundary, and data leaving the machine for every affected path.
- Grant the least privilege needed for the shortest practical duration. Never add `NOPASSWD` sudo rules, including narrow command grants, silently bypass authentication, extend privileged credential timestamps in the background, or grant root-equivalent access through groups, sockets, capabilities, or equivalent interfaces (including Docker group membership).
- Keep secrets, personal data, tokens, and sensitive diagnostic details out of logs, crash reports, screenshots, telemetry, and command-line arguments.
- Size memory-backed `/tmp` deliberately for supported hardware and real workload headroom; keep temporary files private and remove them when their operation finishes.
- Diagnostics must remain local and user initiated. Do not invoke AI services, upload logs, or transmit system information without a separate, explicit user action and a clear preview of the exact data and destination.
- Use private, safely created temporary paths; validate ownership, permissions, symlinks, and path traversal before reading or writing privileged files.
- Fail closed at security boundaries. Do not turn validation or authorization
  failures into success-shaped fallbacks.
- Do not add weak compatibility paths that preserve retired privilege grants,
  leak data, or silently downgrade protections.

## Required review

- Trace the full lifecycle, including setup, normal use, interruption, failure, cleanup, upgrade, and removal.
- Check that errors and debug output do not reveal protected values.
- Add a focused regression only when it exercises real behavior that would fail without the fix; follow the repository test guide.
- Describe the threat boundary and evidence gathered. Report uncertainty rather
  than claiming a security guarantee from a source scan alone.
