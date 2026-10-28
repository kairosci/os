"""Install Linux support for Apple T2 Mac hardware."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile

import yaml


def install_file(target: Path, content: str, mode: str) -> None:
  target.parent.mkdir(parents=True, exist_ok=True)
  with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as temporary:
    temporary.write(content)
    temporary_path = Path(temporary.name)
  try:
    temporary_path.chmod(int(mode, 8))
    os.replace(temporary_path, target)
  finally:
    temporary_path.unlink(missing_ok=True)


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware/apple/t2.yml").read_text(encoding="utf-8"))
  pci = subprocess.run(config["pci_command"], check=False, capture_output=True, text=True)
  if pci.returncode != 0:
    return pci.returncode
  if not re.search(config["pci_pattern"], pci.stdout, re.IGNORECASE):
    return int(config["statuses"]["complete"])

  subprocess.run(config["install_packages"], check=True)
  subprocess.run(config["enable_service"], check=True)
  for item in config["files"]:
    install_file(Path(item["target"]), item["content"], config["mode"])
  return int(config["statuses"]["complete"])


if __name__ == "__main__":
  raise SystemExit(main())
