from __future__ import annotations

import os
import re
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


def _remove_routes(path: Path) -> None:
  if path.is_symlink():
    path.unlink()
  elif path.is_dir():
    shutil.rmtree(path)
  else:
    path.unlink(missing_ok=True)


def main() -> int:
  root = Path(os.environ["ARCH_PATH"])
  config = yaml.safe_load((root / "data/installer/user-setup.yml").read_text(encoding="utf-8"))
  settings = config["asus_mixer_setup"]
  if subprocess.run(settings["predicate"], check=False).returncode:
    return 0

  home = Path.home()
  _copy_atomically(root / settings["wireplumber_source"], home / settings["wireplumber_destination"])
  _remove_routes(home / settings["default_routes"])

  result = subprocess.run(settings["card_command"], check=False, capture_output=True, text=True)
  if result.returncode == 0:
    pattern = re.compile(settings["card_pattern"], re.IGNORECASE)
    card = next((match.group(1) for line in result.stdout.splitlines() if (match := pattern.search(line))), None)
    if card is not None:
      command = [argument.format(card=card) for argument in settings["mixer_command"]]
      return subprocess.run(command, check=False, stderr=subprocess.DEVNULL).returncode
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
