"""Keep the component selector within one valid JSON argv element."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from base_test import CLI_BIN, fail_check, pass_check, test_environment


def main() -> int:
  with tempfile.TemporaryDirectory(prefix="dev-ui-preview-") as temporary_directory:
    scratch = Path(temporary_directory)
    bin_directory = scratch / "bin"
    bin_directory.mkdir()
    log = scratch / "calls.jsonl"
    stub = (
      "#!/usr/bin/python3 -I\n"
      "import json, os, sys\n"
      "with open(os.environ['CALL_LOG'], 'a', encoding='utf-8') as stream:\n"
      "  stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
    )
    executable = bin_directory / "arch-shell"
    executable.write_text(stub, encoding="utf-8")
    executable.chmod(0o755)

    environment = test_environment(CALL_LOG=str(log))
    environment["PATH"] = f"{bin_directory}:{environment['PATH']}"
    if (CLI_BIN / "arch-dev-ui-preview").exists():
      fail_check("UI preview is routed without a flat launcher")

    section = 'button "focus" \\ path'
    result = subprocess.run(
      ["archctl", "dev", "ui", "preview", section],
      capture_output=True,
      text=True,
      env=environment,
      check=False,
    )
    if result.returncode != 0:
      fail_check(f"UI preview route succeeds: {result.stdout}{result.stderr}")
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    expected = ["shell", "summon", "arch.dev-gallery", json.dumps({"section": section}, separators=(",", ":"))]
    if calls != [expected]:
      fail_check(f"UI preview passes an escaped payload in one argument: {calls}")

  pass_check("UI preview routes through Python with an escaped single-argument payload")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
