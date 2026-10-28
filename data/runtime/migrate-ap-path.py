"""Rename the legacy Arch session root in /etc/arch.conf."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import stat
import tempfile


CONFIG = Path("/etc/arch.conf")
LEGACY_VARIABLE = "ARCH_PATH"
VARIABLE = "AP"


def assignment(line: str) -> tuple[str, str] | None:
  try:
    words = shlex.split(line, comments=True, posix=True)
  except ValueError as error:
    raise RuntimeError("/etc/arch.conf contains invalid shell quoting") from error
  if len(words) != 2 or words[0] != "export":
    return None
  name, separator, value = words[1].partition("=")
  if not separator or not value:
    return None
  return name, value


def replace_config(content: str, metadata: os.stat_result) -> None:
  descriptor, temporary_path = tempfile.mkstemp(prefix=".arch.conf.", dir=CONFIG.parent)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as temporary:
      os.fchmod(temporary.fileno(), stat.S_IMODE(metadata.st_mode))
      os.fchown(temporary.fileno(), metadata.st_uid, metadata.st_gid)
      temporary.write(content)
      temporary.flush()
      os.fsync(temporary.fileno())
    os.replace(temporary_path, CONFIG)
    directory = os.open(CONFIG.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory)
    finally:
      os.close(directory)
  finally:
    if os.path.exists(temporary_path):
      os.unlink(temporary_path)


def main() -> int:
  try:
    metadata = CONFIG.lstat()
  except FileNotFoundError:
    return 0
  if not stat.S_ISREG(metadata.st_mode):
    raise RuntimeError("/etc/arch.conf is not a regular file")

  lines = CONFIG.read_text(encoding="utf-8").splitlines(keepends=True)
  matches = [
    (index, parsed)
    for index, line in enumerate(lines)
    if (parsed := assignment(line)) is not None and parsed[0] in {LEGACY_VARIABLE, VARIABLE}
  ]
  if len(matches) > 1:
    raise RuntimeError("/etc/arch.conf has multiple Arch checkout assignments")
  if not matches:
    legacy_assignment = f"export {LEGACY_VARIABLE}"
    if any(line.lstrip().startswith(legacy_assignment) for line in lines):
      raise RuntimeError("/etc/arch.conf has an invalid legacy checkout assignment")
    return 0

  index, (name, value) = matches[0]
  if name == VARIABLE:
    return 0
  if not Path(value).is_absolute():
    raise RuntimeError("/etc/arch.conf checkout path is not absolute")

  ending = next((item for item in ("\r\n", "\n", "\r") if lines[index].endswith(item)), "")
  lines[index] = f"export {VARIABLE}={shlex.quote(value)}{ending}"
  replace_config("".join(lines), metadata)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
