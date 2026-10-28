from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import yaml


def _copy_atomically(source: Path, destination: Path) -> None:
  destination.parent.mkdir(parents=True, exist_ok=True)
  descriptor, temporary = tempfile.mkstemp(dir=destination.parent)
  os.close(descriptor)
  try:
    shutil.copyfile(source, temporary)
    os.chmod(temporary, stat.S_IMODE(source.stat().st_mode))
    os.replace(temporary, destination)
  finally:
    Path(temporary).unlink(missing_ok=True)


def main() -> int:
  root = Path(os.environ["AP"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["vm_setup"]
  if subprocess.run(settings["predicate"], check=False).returncode:
    return 0

  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  print(settings["messages"].get(language, settings["messages"]["en"])["detected"])
  home = Path.home()
  for source, destination in settings["files"]:
    _copy_atomically(root / source, home / destination)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
