"""Check that update status clears the shell indicator without querying updates."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


with tempfile.TemporaryDirectory(prefix="update-status-") as temporary:
  scratch = Path(temporary)
  bin_dir = scratch / "bin"
  bin_dir.mkdir()
  log = scratch / "calls.jsonl"
  stub = (
    "#!/usr/bin/python3 -I\n"
    "import json, os, pathlib, sys\n"
    "with open(os.environ['CALL_LOG'], 'a', encoding='utf-8') as stream:\n"
    "  stream.write(json.dumps([pathlib.Path(sys.argv[0]).name, *sys.argv[1:]]) + '\\n')\n"
  )
  for command in ("arch-update-available", "arch-shell"):
    path = bin_dir / command
    path.write_text(stub, encoding="utf-8")
    path.chmod(0o755)

  environment = test_environment(
    CALL_LOG=log,
    PATH=f"{bin_dir}:{ROOT / 'src/arch/commands'}:/usr/local/bin:/usr/bin",
  )
  result = subprocess.run(
    [str(ROOT / "src/arch/commands/arch-update-status")],
    capture_output=True,
    text=True,
    env=environment,
    check=False,
  )
  if result.returncode != 0:
    fail_check(f"update status clears the indicator: {result.stdout}{result.stderr}")
  calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
  if calls != [["arch-shell", "-q", "arch.system-update", "clear"]]:
    fail_check(f"update status clears without rechecking: {calls}")

pass_check("update status clears the shell indicator without rechecking")
