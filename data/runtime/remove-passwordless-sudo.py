"""Retire Arch-owned passwordless sudo policy during package transactions."""

from __future__ import annotations

import os
from pathlib import Path
import stat


SUDOERS_DIRECTORY = Path("/etc/sudoers.d")
OWNED_RULES = {"arch-dns", "arch-locale-generate", "arch-theme-browser", "arch-tzupdate"}
GENERATED_PREFIXES = ("99-arch-nopasswd-", "99-arch-permanent-nopasswd-")


def backup_path(path: Path) -> Path:
  candidate = path.with_name(f"{path.name}.disabled")
  sequence = 1
  while candidate.exists() or candidate.is_symlink():
    candidate = path.with_name(f"{path.name}.disabled-{sequence}")
    sequence += 1
  return candidate


def owned_rule(name: str) -> bool:
  return name in OWNED_RULES or name.startswith(GENERATED_PREFIXES)


def has_passwordless_rule(path: Path) -> bool:
  try:
    metadata = path.lstat()
  except FileNotFoundError:
    return False
  if stat.S_ISLNK(metadata.st_mode):
    return True
  if not stat.S_ISREG(metadata.st_mode):
    return False
  try:
    return b"NOPASSWD:" in path.read_bytes()
  except OSError as error:
    raise RuntimeError(f"could not inspect {path}") from error


def main() -> int:
  try:
    metadata = SUDOERS_DIRECTORY.lstat()
  except FileNotFoundError:
    return 0
  if not stat.S_ISDIR(metadata.st_mode):
    raise RuntimeError("/etc/sudoers.d is not a real directory")

  for path in sorted(SUDOERS_DIRECTORY.iterdir()):
    if owned_rule(path.name) and has_passwordless_rule(path):
      os.rename(path, backup_path(path))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
