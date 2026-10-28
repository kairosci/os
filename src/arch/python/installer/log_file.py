from __future__ import annotations

import os
import errno
import stat
from pathlib import Path

import yaml


def initialize() -> None:
  root = Path(os.environ["AP"])
  settings = yaml.safe_load((root / "data/installer/logging.yml").read_text(encoding="utf-8"))
  mode = int(settings["install_log"]["file_mode"], 8)
  path = Path(os.environ["ARCH_INSTALL_LOG_FILE"])
  path.parent.mkdir(parents=True, exist_ok=True)
  flags = os.O_WRONLY | os.O_CREAT | os.O_CLOEXEC | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0)
  descriptor = os.open(path, flags, mode)
  try:
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
      raise OSError(errno.EINVAL, os.strerror(errno.EINVAL))
    os.fchmod(descriptor, mode)
  finally:
    os.close(descriptor)


if __name__ == "__main__":
  initialize()
