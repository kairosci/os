from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import yaml


def _write_atomically(destination: Path, content: str, default_mode: int) -> None:
  if destination.is_symlink():
    destination = destination.resolve(strict=True)
  if destination.is_file() and destination.read_text(encoding="utf-8") == content:
    return
  mode = stat.S_IMODE(destination.stat().st_mode) if destination.is_file() else default_mode
  destination.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary = tempfile.mkstemp(dir=destination.parent)
  try:
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
      output.write(content)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, destination)
    directory_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  finally:
    Path(temporary).unlink(missing_ok=True)


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["qualcomm_initramfs"]
  if subprocess.run(settings["platform_check"], check=False).returncode:
    return 0
  directory = Path(os.environ.get(settings["directory_environment"]) or settings["directory_default"])
  destination = directory / settings["filename"]
  content = settings["content"] + "\n"
  _write_atomically(destination, content, int(settings["mode"], 8))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
