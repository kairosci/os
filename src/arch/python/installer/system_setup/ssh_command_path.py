from __future__ import annotations

import os
import re
import stat
import tempfile
from pathlib import Path

import yaml


def _replace_atomically(path: Path, content: str, mode: int) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
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
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/system-setup.yml").read_text(encoding="utf-8"))
  settings = config["ssh_command_path"]
  path = Path(settings["file"])
  if path.is_symlink():
    path = path.resolve(strict=False)
  original = path.read_text(encoding="utf-8") if path.is_file() else ""
  if re.search(settings["path_pattern"], original, flags=re.MULTILINE):
    return 0

  updated = original + settings["append_content"] + "\n"
  mode = stat.S_IMODE(path.stat().st_mode) if path.is_file() else int(settings["file_mode"], 8)
  _replace_atomically(path, updated, mode)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
