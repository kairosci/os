"""Check that fingerprint setup waits for hardware and launches once."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from base_test import ROOT, fail_check, pass_check, test_environment


HOOK = ROOT / "installer/user/first-run/setup-fingerprint.hook"
DESCRIPTION = "fingerprint invitation waits for a reader and only runs once"


def executable(path: Path, content: str) -> None:
  path.write_text(content, encoding="utf-8")
  path.chmod(0o700)


def run_hook(hook_path: Path, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
  shutil.copyfile(HOOK, hook_path)
  return subprocess.run(
    ["bash", str(hook_path)],
    env=environment,
    check=False,
    capture_output=True,
    text=True,
  )


def main() -> int:
  if Path("/etc/pam.d/arch-lock-fingerprint").is_file():
    print(f"ok - {DESCRIPTION} # SKIP")
    return 0

  try:
    with tempfile.TemporaryDirectory() as temporary:
      work = Path(temporary)
      home = work / "home"
      bin_directory = work / "bin"
      home.mkdir()
      bin_directory.mkdir()
      log = work / "events"
      log.touch()
      marker = work / "hardware-present"
      hook_path = home / ".config/arch/hooks/post-update.d/setup-fingerprint.hook"
      hook_path.parent.mkdir(parents=True)

      executable(bin_directory / "arch-hw-fingerprint", "#!/bin/bash\n[[ -f $TEST_HW_MARKER ]]\n")
      executable(
        bin_directory / "arch-notification-send",
        '#!/bin/bash\n'
        'echo notification >>"$TEST_LOG"\n'
        'while (($# > 0)); do\n'
        '  if [[ $1 == "--exec" ]]; then\n'
        '    shift\n'
        '    echo "exec:$*" >>"$TEST_LOG"\n'
        '    break\n'
        '  fi\n'
        '  shift\n'
        'done\n',
      )
      executable(bin_directory / "systemd-run", '#!/bin/bash\necho "systemd-run:$*" >>"$TEST_LOG"\n')
      environment = test_environment(
        HOME=home,
        PATH=f"{bin_directory}:{ROOT / 'src/cli'}:{os.environ.get('PATH', '')}",
        TEST_LOG=log,
        TEST_HW_MARKER=marker,
      )

      result = run_hook(hook_path, environment)
      if result.returncode != 0:
        fail_check(result.stdout + result.stderr)
      done = home / ".local/state/arch/done/fingerprint-setup-invitation"
      if done.exists() or log.read_text(encoding="utf-8"):
        fail_check("invitation remains pending when no reader is present")

      marker.touch()
      result = run_hook(hook_path, environment)
      if result.returncode != 0:
        fail_check(result.stdout + result.stderr)
      events = log.read_text(encoding="utf-8").splitlines()
      if not done.is_file() or not hook_path.is_file() or events.count("notification") != 1:
        fail_check("invitation records completion and sends one notification")
      if "exec:arch-launch-terminal arch-setup-security-fingerprint" not in events:
        fail_check("invitation launches setup in a tiling terminal")
      if any(event.startswith("systemd-run:") for event in events):
        fail_check("invitation does not start a background unit")

      result = run_hook(hook_path, environment)
      if result.returncode != 0:
        fail_check(result.stdout + result.stderr)
      if log.read_text(encoding="utf-8").splitlines().count("notification") != 1:
        fail_check("completed invitation does not notify a second time")
  except (OSError, AssertionError, subprocess.SubprocessError) as error:
    fail_check(str(error))

  pass_check(DESCRIPTION)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
