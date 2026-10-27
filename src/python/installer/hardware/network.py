from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml


def _run(command: list[str]) -> subprocess.CompletedProcess[str] | None:
  try:
    return subprocess.run(command, check=False, stderr=subprocess.DEVNULL)
  except OSError:
    return None


def _is_stock_networkd_file(path: Path, settings: dict[str, object]) -> bool:
  if not path.is_file() or path.name not in settings["network_files"]:
    return False
  try:
    content = path.read_text(encoding="utf-8", errors="replace")
  except OSError:
    return False
  return (
    re.search(settings["dhcp_pattern"], content, flags=re.MULTILINE) is not None
    and re.search(settings["interface_pattern"], content, flags=re.MULTILINE) is not None
  )


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["network_setup"]
  systemctl = settings["systemctl_command"]

  for unit in settings["disable_units"]:
    _run([*systemctl, "disable", unit])
  for unit in settings["mask_units"]:
    _run([*systemctl, "mask", unit])

  network_directory = Path(settings["network_directory"])
  timestamp = datetime.now().astimezone().strftime(settings["timestamp_format"])
  backup_directory = network_directory / settings["backup_directory_template"].format(timestamp=timestamp)
  for filename in settings["network_files"]:
    source = network_directory / filename
    if _is_stock_networkd_file(source, settings):
      backup_directory.mkdir(mode=0o755, parents=True, exist_ok=True)
      os.chmod(backup_directory, 0o755)
      shutil.move(str(source), str(backup_directory))

  manager_active = _run(settings["manager_active_command"])
  if manager_active is not None and manager_active.returncode == 0:
    _run([*settings["stop_command"]])
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
