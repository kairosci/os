"""Verify firewall setup installs rules without activating UFW immediately."""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


SETUP = ROOT / "src/arch/python/installer/system_setup/firewall.py"
UFw_MOCK = """#!/usr/bin/python3
import os
from pathlib import Path
import sys

with Path(os.environ["TEST_LOG"]).open("a", encoding="utf-8") as log:
  log.write(f"ufw {' '.join(sys.argv[1:])}\\n")
if sys.argv[1:] == ["status"]:
  print("Status: inactive")
"""
UFw_DOCKER_MOCK = """#!/usr/bin/python3
PATH="/bin:/usr/bin:/sbin:/usr/sbin:/snap/bin/"
import os
from pathlib import Path
import subprocess
import sys

os.environ["PATH"] = PATH
with Path(os.environ["TEST_LOG"]).open("a", encoding="utf-8") as log:
  log.write(f"ufw-docker {' '.join(sys.argv[1:])}\\n")
status = subprocess.run(["ufw", "status"], check=False, capture_output=True, text=True)
if "Status: active" not in status.stdout:
  print("inactive", file=sys.stderr)
  raise SystemExit(1)
"""
SYSTEMCTL_MOCK = """#!/usr/bin/python3
import os
from pathlib import Path
import sys

with Path(os.environ["TEST_LOG"]).open("a", encoding="utf-8") as log:
  log.write(f"systemctl {' '.join(sys.argv[1:])}\\n")
"""


def main() -> int:
  with tempfile.TemporaryDirectory() as temporary_directory:
    temporary = Path(temporary_directory)
    mock_bin = temporary / "bin"
    mock_bin.mkdir()
    log_path = temporary / "firewall.log"
    config_path = temporary / "ufw.conf"
    config_path.write_text("ENABLED=no\n", encoding="utf-8")

    for name, source in (
      ("ufw", UFw_MOCK),
      ("ufw-docker", UFw_DOCKER_MOCK),
      ("systemctl", SYSTEMCTL_MOCK),
    ):
      executable = mock_bin / name
      executable.write_text(source, encoding="utf-8")
      executable.chmod(0o755)

    environment = test_environment(
      ARCH_UFW_CONFIG=str(config_path),
      TEST_LOG=str(log_path),
    )
    environment["PATH"] = f"{mock_bin}:{environment['PATH']}"
    result = subprocess.run(
      ["python3", "-I", str(SETUP)],
      check=False,
      env=environment,
      capture_output=True,
      text=True,
    )
    if result.returncode != 0:
      fail_check("firewall setup completes successfully")

    calls = log_path.read_text(encoding="utf-8").splitlines()
    if "ufw-docker install" not in calls:
      fail_check("ufw-docker rules are installed")
    if "systemctl enable ufw" not in calls:
      fail_check("ufw is enabled for next boot")
    if "systemctl start ufw" in calls:
      fail_check("firewall setup does not activate UFW immediately")
    if config_path.read_text(encoding="utf-8") != "ENABLED=yes\n":
      fail_check("UFW is enabled for the next boot in its configuration")
    pass_check("firewall config installs ufw-docker rules without activating live UFW")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
