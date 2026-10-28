from __future__ import annotations

import os
import secrets
import stat
import sys
import time
from pathlib import Path

import yaml


def _write_all(descriptor: int, content: bytes) -> None:
  remaining = memoryview(content)
  while remaining:
    written = os.write(descriptor, remaining)
    if written <= 0:
      raise OSError("keyring write made no progress")
    remaining = remaining[written:]


def _install_file(directory_fd: int, name: str, content: bytes, mode: int) -> None:
  flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
  stage = f".{name}.{secrets.token_hex(16)}.tmp"
  descriptor = os.open(stage, flags, mode, dir_fd=directory_fd)
  try:
    _write_all(descriptor, content)
    os.fsync(descriptor)
    try:
      os.link(stage, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd, follow_symlinks=False)
    except FileExistsError:
      pass
  finally:
    os.close(descriptor)
    os.unlink(stage, dir_fd=directory_fd)

  safe_flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
  existing = os.open(name, safe_flags, dir_fd=directory_fd)
  try:
    if not stat.S_ISREG(os.fstat(existing).st_mode):
      raise OSError("keyring path is not a regular file")
    os.fchmod(existing, mode)
  finally:
    os.close(existing)


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["default_keyring"]
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  message = settings["messages"].get(language, settings["messages"]["en"])["setup_failed"]
  directory = Path.home() / settings["directory"]
  try:
    directory.mkdir(parents=True, exist_ok=True)
    directory_fd = os.open(
      directory,
      os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
      os.fchmod(directory_fd, int(settings["directory_mode"], 8))
      keyring = settings["keyring_content"].format(ctime=int(time.time())) + "\n"
      _install_file(
        directory_fd,
        settings["keyring_file"],
        keyring.encode("utf-8"),
        int(settings["keyring_mode"], 8),
      )
      _install_file(
        directory_fd,
        settings["default_file"],
        (settings["default_content"] + "\n").encode("utf-8"),
        int(settings["default_mode"], 8),
      )
    finally:
      os.close(directory_fd)
  except OSError:
    print(message, file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
