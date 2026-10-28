"""Preserve the T2 repository when pacman configuration is restored."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import re
import stat
import subprocess

import yaml


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load(
    (root / "data/installer/hardware/pacman-repositories.yml").read_text(encoding="utf-8"),
  )
  status = int(config["statuses"]["complete"])
  try:
    pci = subprocess.run(config["pci_command"], check=False, capture_output=True, text=True)
  except OSError:
    return status
  if re.search(config["device_pattern"], pci.stdout) is None:
    return status

  target = Path(
    os.environ.get(config["config_environment"]) or config["config_default"],
  )
  flags = os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
  descriptor = os.open(target, flags, int(config["file_mode"], 8))
  with os.fdopen(descriptor, "a+", encoding="utf-8") as pacman_config:
    fcntl.flock(pacman_config.fileno(), fcntl.LOCK_EX)
    if not stat.S_ISREG(os.fstat(pacman_config.fileno()).st_mode):
      language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
      messages = config["messages"].get(language, config["messages"]["en"])
      raise OSError(messages["invalid_config"])
    pacman_config.seek(0)
    if config["repository_header"] in pacman_config.read().splitlines():
      return status
    pacman_config.seek(0, os.SEEK_END)
    pacman_config.write(config["append_prefix"] + config["repository_content"])
    pacman_config.flush()
    os.fsync(pacman_config.fileno())
  return status


if __name__ == "__main__":
  raise SystemExit(main())
