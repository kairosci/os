from __future__ import annotations

import os
import re
import stat
import tempfile
from pathlib import Path

import yaml


def _replace_atomically(path: Path, content: str, mode: int) -> None:
  if path.is_symlink():
    path = path.resolve(strict=True)
  descriptor, temporary = tempfile.mkstemp(dir=path.parent)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(content)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  finally:
    Path(temporary).unlink(missing_ok=True)


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/system-setup.yml").read_text(encoding="utf-8"))
  settings = config["powerprofilesctl_shebang"]
  path = Path(settings["file"])
  if not path.is_file():
    return 0

  original = path.read_text(encoding="utf-8")
  updated = re.sub(settings["match_pattern"], settings["replacement"], original, flags=re.MULTILINE)
  if updated != original:
    _replace_atomically(path, updated, stat.S_IMODE(path.stat().st_mode))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
