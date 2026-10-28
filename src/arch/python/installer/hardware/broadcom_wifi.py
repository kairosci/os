from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["broadcom_wifi_setup"]
  result = subprocess.run(settings["pci_command"], check=False, stdout=subprocess.PIPE, text=True)
  if result.returncode:
    return result.returncode
  inventory = result.stdout.lower()
  if not any(device_id.lower() in inventory for device_id in settings["device_ids"]):
    return 0

  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  print(settings["detected_message"].get(language, settings["detected_message"]["en"]))
  return subprocess.run(settings["package_command"], check=False).returncode


if __name__ == "__main__":
  raise SystemExit(main())
