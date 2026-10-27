"""Check font installation inputs reject shell and XML injection."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


with tempfile.TemporaryDirectory(prefix="install-font-") as temporary:
  scratch = Path(temporary)
  bin_dir = scratch / "bin"
  bin_dir.mkdir()
  log = scratch / "calls.jsonl"
  stub = (
    "#!/usr/bin/python3 -I\n"
    "import json, os, pathlib, sys\n"
    "with open(os.environ['FONT_LOG'], 'a', encoding='utf-8') as stream:\n"
    "  stream.write(json.dumps([pathlib.Path(sys.argv[0]).name, *sys.argv[1:]]) + '\\n')\n"
  )
  for command in ("arch-pkg-add", "fc-cache", "arch-font-set"):
    path = bin_dir / command
    path.write_text(stub, encoding="utf-8")
    path.chmod(0o755)

  environment = test_environment(
    FONT_LOG=log,
    PATH=f"{bin_dir}:{ROOT / 'src/cli'}:{Path('/usr/local/bin')}:{Path('/usr/bin')}",
  )
  install = str(ROOT / "src/cli/arch-install-font")
  result = subprocess.run(
    [install, "--apply", "ttf-example", "Family Example"],
    capture_output=True,
    text=True,
    env=environment,
    check=False,
  )
  if result.returncode != 0:
    fail_check(f"preferred font installation: {result.stdout}{result.stderr}")

  calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
  expected = [
    ["arch-pkg-add", "ttf-example"],
    ["fc-cache", "-f"],
    ["arch-font-set", "Family Example"],
  ]
  if calls != expected:
    fail_check(f"preferred font installation and activation: {calls}")
  pass_check("preferred font installation and activation")

  log.write_text("", encoding="utf-8")
  for values, description in (
    (["ttf-example;touch /tmp/pwned", "Family Example"], "package input cannot contain shell commands"),
    (["ttf-example", 'Family"</string><evil>'], "font family input cannot inject XML"),
  ):
    result = subprocess.run(
      [install, "--apply", *values],
      capture_output=True,
      text=True,
      env=environment,
      check=False,
    )
    if result.returncode == 0:
      fail_check(description)
  if log.read_text(encoding="utf-8"):
    fail_check("invalid font values are rejected before installation")
  pass_check("font package and family input are validated before installation")
