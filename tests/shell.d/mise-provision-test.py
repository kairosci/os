"""Check per-user mise setup and ensure it declares no agent tools."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib

from base_test import ROOT, fail_check, pass_check, test_environment


with tempfile.TemporaryDirectory(prefix="mise-setup-") as temporary:
  scratch = Path(temporary)
  bin_dir = scratch / "bin"
  home = scratch / "home with spaces"
  bin_dir.mkdir()
  (home / ".local/bin").mkdir(parents=True)
  log = scratch / "mise-log"
  stub = bin_dir / "mise"
  stub.write_text(
    "#!/usr/bin/python3 -I\n"
    "import json, os, sys\n"
    "with open(os.environ['ARCH_TEST_MISE_LOG'], 'a', encoding='utf-8') as stream:\n"
    "  stream.write(json.dumps(sys.argv[1:]) + '\\n')\n",
    encoding="utf-8",
  )
  stub.chmod(0o755)
  environment = test_environment(
    HOME=home,
    ARCH_TEST_MISE_LOG=log,
    PATH=f"{bin_dir}:{home / '.local/bin'}:{ROOT / 'src/cli'}:/usr/local/bin:/usr/bin",
  )
  result = subprocess.run(
    [sys.executable, "-I", str(ROOT / "src/python/installer_user/setup/mise.py")],
    capture_output=True,
    text=True,
    env=environment,
    check=False,
  )
  if result.returncode != 0:
    fail_check(f"user mise setup completes: {result.stdout}{result.stderr}")
  calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
  if calls != [["reshim", "--system"], ["reshim"]]:
    fail_check(f"user mise setup only refreshes declared shims: {calls}")

  tools = tomllib.loads((ROOT / "etc/mise/conf.d/arch-tools.toml").read_text(encoding="utf-8"))["tools"]
  agent_tools = {"codex", "claude", "kimi", "cursor-agent", "muse"}
  if agent_tools.intersection(tools):
    fail_check(f"mise does not declare agent tools or their shims: {sorted(agent_tools.intersection(tools))}")
  pass_check("user mise setup only refreshes declared shims and declares no agent tools")

user_config = (ROOT / "etc/mise/conf.d/arch.toml").read_text(encoding="utf-8").splitlines()
if "upgrade.auto_prune = false" not in user_config:
  fail_check("os's mise config keeps upgrades from pruning versions still in use")
pass_check("upgrade pruning is off in the package-owned mise config")
