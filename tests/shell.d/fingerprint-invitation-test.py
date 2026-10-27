"""Check that fingerprint setup waits for hardware and launches once."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from base_test import ROOT, fail_check, pass_check, test_environment


HOOK_SOURCE = ROOT / "src/python/installer_user/first_run/fingerprint_invitation.py"
HOOK_RUNNER = ROOT / "src/commands/arch-hook"
DESCRIPTION = "fingerprint invitation waits for a reader and only runs once"


def executable(path: Path, content: str) -> None:
  path.write_text(content, encoding="utf-8")
  path.chmod(0o700)


def run_hook(environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [str(HOOK_RUNNER), "post-update"],
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
      hook_directory = home / ".config/arch/hooks/post-update.d"
      home.mkdir()
      bin_directory.mkdir()
      hook_directory.mkdir(parents=True)
      hook = hook_directory / "fingerprint_invitation.py"
      shutil.copyfile(HOOK_SOURCE, hook)

      log = work / "events"
      log.touch()
      marker = work / "hardware-present"
      executable(bin_directory / "arch-hw-fingerprint", "#!/bin/bash\n[[ -f $TEST_HW_MARKER ]]\n")
      executable(
        bin_directory / "arch-notification-send",
        '#!/bin/bash\nprintf \'%s\\0\' "$@" >>"$TEST_LOG"\nprintf \'\\0\' >>"$TEST_LOG"\n',
      )
      environment = test_environment(
        HOME=home,
        LANG="it_IT.UTF-8",
        PATH=f"{bin_directory}:{ROOT / 'src/commands'}:{os.environ.get('PATH', '')}",
        TEST_LOG=log,
        TEST_HW_MARKER=marker,
      )
      log_arguments = lambda: [item.decode() for item in log.read_bytes().split(b"\0") if item]

      result = run_hook(environment)
      if result.returncode != 0:
        fail_check(result.stdout + result.stderr)
      done = home / ".local/state/arch/done/fingerprint-setup-invitation"
      if done.exists() or log_arguments():
        fail_check("invitation remains pending when no reader is present")

      marker.touch()
      result = run_hook(environment)
      if result.returncode != 0:
        fail_check(result.stdout + result.stderr)
      arguments = log_arguments()
      if not done.is_file() or not hook.is_file() or arguments.count("-u") != 1:
        fail_check("invitation records completion and sends one notification")
      config = yaml.safe_load((ROOT / "data/installer/first-run.yml").read_text(encoding="utf-8"))
      title = config["fingerprint_invitation"]["notification"]["messages"]["it"]["title"]
      if title not in arguments:
        fail_check("fingerprint notification uses its Italian YAML translation")
      action = arguments.index("--exec") if "--exec" in arguments else -1
      if action < 0 or arguments[action + 1:action + 3] != ["arch-launch-terminal", "arch-setup-security-fingerprint"]:
        fail_check("invitation launches setup in a tiling terminal")

      result = run_hook(environment)
      if result.returncode != 0:
        fail_check(result.stdout + result.stderr)
      if log_arguments().count("-u") != 1:
        fail_check("completed invitation does not notify a second time")
  except (OSError, AssertionError, subprocess.SubprocessError) as error:
    fail_check(str(error))

  pass_check(DESCRIPTION)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
