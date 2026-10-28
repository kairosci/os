from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml


def _create_atomically(path: Path, content: str, mode: int, directory_mode: int) -> None:
  parent_exists = path.parent.exists()
  path.parent.mkdir(parents=True, exist_ok=True, mode=directory_mode)
  if not parent_exists:
    os.chmod(path.parent, directory_mode)
  descriptor, temporary = tempfile.mkstemp(dir=path.parent)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(content)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, mode)
    try:
      os.link(temporary, path)
    except FileExistsError:
      return
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
  settings = config["ssh_keepalive"]
  _create_atomically(
    Path(settings["path"]),
    settings["content"] + "\n",
    int(settings["file_mode"], 8),
    int(settings["directory_mode"], 8),
  )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
