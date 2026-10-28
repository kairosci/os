from __future__ import annotations

import errno
import os
import secrets
import subprocess
from pathlib import Path

import yaml


def _create_once(path: Path, content: bytes, mode: int) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  stage = path.parent / f".{path.name}.{secrets.token_hex(16)}.tmp"
  flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
  descriptor = os.open(stage, flags, mode)
  try:
    remaining = memoryview(content)
    while remaining:
      written = os.write(descriptor, remaining)
      if written <= 0:
        raise OSError(errno.EIO, os.strerror(errno.EIO))
      remaining = remaining[written:]
    os.fsync(descriptor)
    try:
      os.link(stage, path, follow_symlinks=False)
    except FileExistsError:
      pass
  finally:
    os.close(descriptor)
    stage.unlink(missing_ok=True)


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["apple_keyboard_fkeys"]
  if subprocess.run(settings["apple_predicate"], check=False).returncode == 0:
    return 0
  destination = Path(os.environ.get(settings["config_environment"], settings["config_default"]))
  if destination.is_file():
    return 0
  _create_once(destination, settings["content"].encode("utf-8"), int(settings["mode"], 8))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
