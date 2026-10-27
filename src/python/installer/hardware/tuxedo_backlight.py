from __future__ import annotations

import glob
import os
import re
import stat
import subprocess
import tempfile
from pathlib import Path

import yaml


def _write_atomically(destination: Path, content: str, default_mode: int) -> None:
  if destination.is_symlink():
    destination = destination.resolve(strict=True)
  previous = destination.read_text(encoding="utf-8") if destination.is_file() else None
  if previous == content:
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


def _remove_unowned_modules(settings: dict[str, object]) -> None:
  pattern = re.compile(settings["unowned_pattern"])
  environment = {**os.environ, **settings["ownership_environment"]}
  for filename in sorted(glob.glob(settings["module_glob"])):
    path = Path(filename)
    if not path.is_file():
      continue
    result = subprocess.run(
      [*settings["ownership_command"], str(path)],
      check=False,
      capture_output=True,
      text=True,
      env=environment,
    )
    if result.returncode == 0:
      continue
    if pattern.search(result.stderr) is None:
      continue
    path.unlink()


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/hardware.yml").read_text(encoding="utf-8"))
  settings = config["tuxedo_backlight_setup"]
  try:
    vendor = Path(settings["vendor_file"]).read_text(encoding="utf-8", errors="replace")
  except OSError:
    return 0
  if re.search(settings["vendor_pattern"], vendor, flags=re.IGNORECASE) is None:
    return 0

  result = subprocess.run([*settings["package_command"], settings["package"]], check=False)
  if result.returncode:
    return result.returncode
  _write_atomically(
    Path(settings["blacklist_file"]),
    settings["blacklist_content"],
    int(settings["mode"], 8),
  )
  _remove_unowned_modules(settings)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
