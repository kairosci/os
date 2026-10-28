"""Verify security setup creates polkit PAM stacks with faillock enabled."""

from __future__ import annotations

from pathlib import Path
import re

from base_test import ROOT, fail_check, pass_check


SETUPS = (
  "arch-setup-security-fingerprint",
  "arch-setup-security-fido2",
)
PHASES = ("auth", "account", "password", "session")


def pam_stack(source: str) -> str:
  lines = source.splitlines()
  start = next((index for index, line in enumerate(lines) if "tee /etc/pam.d/polkit-1" in line), None)
  if start is None:
    return ""
  end = next((index for index in range(start, len(lines)) if lines[index] == "EOF"), None)
  if end is None:
    return ""
  return "\n".join(lines[start:end + 1])


def main() -> int:
  for setup in SETUPS:
    source = (ROOT / "src/commands" / setup).read_text(encoding="utf-8")
    body = pam_stack(source)
    if not body:
      fail_check(f"{setup} writes a polkit-1 stack")

    for phase in PHASES:
      pattern = rf"^{phase}[\t ]+include[\t ]+system-auth(?:[\t ]|$)"
      if re.search(pattern, body, re.MULTILINE) is None:
        fail_check(f"{setup} polkit-1 {phase} defers to system-auth")

    if re.search(r"^(?:account|password|session)[\t ]+required[\t ]+pam_unix", body, re.MULTILINE):
      fail_check(f"{setup} does not hand-roll a bare pam_unix stack")
    pass_check(f"{setup} creates a polkit-1 stack that includes system-auth")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
