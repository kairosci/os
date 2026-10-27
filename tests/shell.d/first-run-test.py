#!/usr/bin/python3

"""Verify the first-run lifecycle gate and its localized help."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


COMMAND = ROOT / "src/commands/arch-provision-first-run"


def write_executable(path: Path, source: str) -> None:
  path.write_text(source, encoding="utf-8")
  path.chmod(0o755)


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary:
    temp = Path(temporary)
    mock_bin = temp / "bin"
    home = temp / "home"
    mock_bin.mkdir()
    home.mkdir()

    write_executable(
      mock_bin / "arch-done",
      "#!/usr/bin/python3\n"
      "import os, sys\n"
      "sys.exit(0 if sys.argv[1:] == ['check', 'first-run-user'] and os.getenv('ARCH_TEST_DONE') == '1' else 1)\n",
    )
    write_executable(
      mock_bin / "arch-provision-user",
      "#!/usr/bin/python3\n"
      "import os\n"
      "from pathlib import Path\n"
      "Path(os.environ['ARCH_TEST_FINALIZE_CALLED']).touch()\n",
    )

    environment = test_environment(
      HOME=str(home),
      PATH=f"{mock_bin}:{os.environ.get('PATH', '')}",
      ARCH_TEST_DONE="1",
      ARCH_TEST_FINALIZE_CALLED=str(temp / "finalize-called"),
    )
    completed = subprocess.run([COMMAND], check=False, capture_output=True, text=True, env=environment)
    marker = Path(environment["ARCH_TEST_FINALIZE_CALLED"])
    if completed.returncode != 0:
      fail_check("completed first-run exits before setup")
    if marker.exists():
      fail_check("completed first-run exits before setup")
    pass_check("completed first-run exits before setup")
    if "First-run already complete." not in completed.stdout:
      fail_check("completed first-run reports its lifecycle gate")
    pass_check("completed first-run reports its lifecycle gate")

    help_environment = test_environment(LANG="it_IT.UTF-8")
    help_output = subprocess.run(
      [COMMAND, "--help"], check=False, capture_output=True, text=True, env=help_environment
    )
    if help_output.returncode != 0 or "Esegue la configurazione iniziale" not in help_output.stdout:
      fail_check("first-run help uses the Italian YAML strings")
    pass_check("first-run help uses the Italian YAML strings")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
