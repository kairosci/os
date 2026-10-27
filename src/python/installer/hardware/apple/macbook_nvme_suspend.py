"""Install the NVMe suspend workaround on affected MacBook models."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/apple/macbook-nvme-suspend.yml").read_text(encoding="utf-8"),
  )
  matched = any(
    subprocess.run([*config["match_command"], model], check=False).returncode == 0
    for model in config["models"]
  )
  if not matched or not Path(config["nvme_device"]).is_file():
    return int(config["statuses"]["complete"])

  with tempfile.TemporaryDirectory() as temporary_directory:
    source = Path(temporary_directory) / Path(config["service_target"]).name
    source.write_text(config["service_content"], encoding="utf-8")
    subprocess.run([*config["install_file"], str(source), config["service_target"]], check=True)
  subprocess.run([*config["enable_service"], Path(config["service_target"]).name], check=True)
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
