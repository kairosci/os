"""Check that the presentation wrapper launches the Arch terminal."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


with tempfile.TemporaryDirectory(prefix="presentation-terminal-") as temporary:
  scratch = Path(temporary)
  bin_dir = scratch / "bin"
  bin_dir.mkdir()
  log = scratch / "launch"
  launcher_stub = bin_dir / "setsid"
  launcher_stub.write_text(
    "#!/usr/bin/python3 -I\n"
    "import os, sys\n"
    "from pathlib import Path\n"
    "Path(os.environ['TEST_LOG']).write_text(' '.join(sys.argv[1:]), encoding='utf-8')\n",
    encoding="utf-8",
  )
  launcher_stub.chmod(0o755)
  environment = test_environment(TEST_LOG=log)
  environment["PATH"] = f"{bin_dir}:{environment['PATH']}"
  result = subprocess.run(
    [str(ROOT / "src/commands/arch-launch-terminal-with-presentation"), "echo hello"],
    capture_output=True,
    text=True,
    env=environment,
    check=False,
  )
  if result.returncode != 0:
    fail_check(f"presentation terminal launch: {result.stdout}{result.stderr}")
  launch = log.read_text(encoding="utf-8")
  if "xdg-terminal-exec --app-id=org.arch.terminal" not in launch:
    fail_check(f"presentation terminal launches the Arch terminal: {launch}")

pass_check("presentation terminal launches the Arch terminal")
