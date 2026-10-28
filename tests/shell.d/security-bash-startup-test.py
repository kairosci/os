"""Verify privileged Bash checks prove the shell started in privileged mode."""

from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


LIBRARY = ROOT / "src/commands/arch-security-functions"
CHECK = "arch_security_require_privileged_bash_startup"
UNSHARE = shutil.which("unshare")
BASH = "/usr/bin/bash"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    command,
    check=False,
    env=test_environment(),
    stdin=subprocess.DEVNULL,
    capture_output=True,
    text=True,
  )


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary_directory:
    temporary = Path(temporary_directory)
    entrypoint = temporary / "entrypoint"
    late = temporary / "late"
    library_path = shlex.quote(str(LIBRARY))
    entrypoint.write_text(
      f"#!/bin/bash -p\nsource {library_path}\n{CHECK} && ( {CHECK} )\n",
      encoding="utf-8",
    )
    late.write_text(f"set -p\nsource {library_path}\n{CHECK}\n", encoding="utf-8")
    entrypoint.chmod(0o755)

    result = run([str(entrypoint)])
    if result.returncode != 0:
      fail_check("a script started as bash -p passes the startup check in a subshell")
    pass_check("a script started as bash -p passes the startup check in a subshell")

    for arguments in ([], ["-p"]):
      result = run([BASH, str(late), *arguments])
      if result.returncode == 0:
        fail_check(f"Bash that only enables -p later is rejected (arguments: {arguments})")
    result = run([BASH, str(entrypoint)])
    if result.returncode == 0:
      fail_check("a script not started with -p is rejected")
    pass_check("Bash not started with -p is rejected regardless of later options")

    if UNSHARE is None:
      print("ok - a new PID namespace check # SKIP")
      return 0
    namespace = [UNSHARE, "--user", "--map-root-user", "--fork", "--pid"]
    available = run([*namespace, "/usr/bin/true"])
    if available.returncode != 0:
      print("ok - a new PID namespace check # SKIP")
      return 0

    nested = f"for i in {{1..50}}; do /usr/bin/true; done; {shlex.quote(str(entrypoint))}; exit"
    result = run([*namespace, BASH, "-c", nested])
    if result.returncode != 0:
      fail_check("the startup check passes in a new PID namespace")
    pass_check("the startup check passes in a new PID namespace")

    late_nested = f"for i in {{1..50}}; do /usr/bin/true; done; {BASH} {shlex.quote(str(late))} -p; exit"
    result = run([*namespace, BASH, "-c", late_nested])
    if result.returncode == 0:
      fail_check("Bash that only enables -p later is rejected in a new PID namespace")
    pass_check("the startup check sees its caller in a new PID namespace")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
