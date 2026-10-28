"""Keep the DGX Spark boot configuration compatible with Direct Boot."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/nvidia/dgx-spark-boot.yml").read_text(encoding="utf-8"),
  )
  statuses = config["statuses"]
  if subprocess.run(config["hardware_check"], check=False).returncode != int(statuses["complete"]):
    return int(statuses["complete"])
  if subprocess.run(config["model_check"], check=False).returncode != int(statuses["complete"]):
    return int(statuses["complete"])

  directory = Path(
    os.environ.get(config["config_directory_environment"]) or config["config_directory_default"],
  )
  target = directory / config["config_filename"]
  direct_boot_status = subprocess.run(config["direct_boot_check"], check=False).returncode
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = config["messages"].get(language, config["messages"]["en"])
  if direct_boot_status == int(statuses["direct_boot"]):
    target.unlink(missing_ok=True)
    print(messages["direct_boot"])
  elif direct_boot_status == int(statuses["not_direct_boot"]):
    directory.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=directory, prefix=f"{target.name}.")
    temporary = Path(temporary_name)
    try:
      with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(config["dropin_content"])
      temporary.chmod(int(config["file_mode"], 8))
      os.replace(temporary, target)
    finally:
      temporary.unlink(missing_ok=True)
    print(messages["setting_applied"])
  else:
    print(messages["efi_unreadable"], file=sys.stderr)
  return int(statuses["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
