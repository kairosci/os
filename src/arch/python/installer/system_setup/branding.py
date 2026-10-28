from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def _settings() -> tuple[Path, dict[str, Any]]:
  ap = Path(os.environ["ARCH_PATH"])
  with (ap / "data/installer/branding-setup.yml").open(encoding="utf-8") as stream:
    settings = yaml.safe_load(stream)
  if not isinstance(settings, dict):
    raise ValueError("invalid branding setup settings")
  return ap, settings["branding"]


def _backup_directory(settings: dict[str, Any]) -> Path:
  backup = settings["backup_directory"]
  timestamp = datetime.now().astimezone().strftime(backup["timestamp_format"])
  return Path(backup["parent"]) / f'{backup["name"]}-{timestamp}'


def _backup(path: Path, backup_dir: Path) -> None:
  destination = backup_dir / path.relative_to(path.anchor)
  destination.parent.mkdir(parents=True, exist_ok=True)
  if path.is_symlink():
    destination.symlink_to(os.readlink(path))
  elif path.is_dir():
    shutil.copytree(path, destination, symlinks=True, dirs_exist_ok=True)
  else:
    shutil.copy2(path, destination, follow_symlinks=False)


def _replace_file(source: Path, target: Path, mode: int, backup_dir: Path) -> None:
  target.parent.mkdir(parents=True, exist_ok=True)
  if target.is_file() and not target.is_symlink() and source.read_bytes() == target.read_bytes():
    return
  if target.exists() or target.is_symlink():
    _backup(target, backup_dir)

  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as output, source.open("rb") as input_stream:
      shutil.copyfileobj(input_stream, output)
      output.flush()
      os.fsync(output.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, target)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def _target(entry: dict[str, str]) -> Path:
  if "target_environment" in entry:
    parent = os.environ.get(entry["target_environment"], entry["target_default"])
    return Path(parent) / entry["target_name"]
  return Path(entry["target"])


def main() -> None:
  ap, settings = _settings()
  backup_dir = _backup_directory(settings)
  mode = int(settings["installed_file_mode"], 8)

  for entry in settings["files"]:
    _replace_file(ap / entry["source"], _target(entry), mode, backup_dir)

  for entry in settings["trees"]:
    shutil.copytree(ap / entry["source"], entry["target"], symlinks=True, dirs_exist_ok=True)

  for entry in settings["tree_files"]:
    _replace_file(ap / entry["source"], Path(entry["target"]), mode, backup_dir)

  for entry in settings["skeleton_files"]:
    _replace_file(ap / entry["source"], Path(entry["target"]), mode, backup_dir)

  plymouth = settings["plymouth"]
  if plymouth["expected_line"] not in Path(plymouth["config"]).read_text(encoding="utf-8").splitlines():
    subprocess.run(plymouth["command"], check=True)

  boot_name = settings["boot_name"]
  for value in settings["boot_configs"]:
    path = Path(value)
    if not path.is_file():
      continue
    original = path.read_text(encoding="utf-8")
    if boot_name["match"] not in original:
      continue
    _backup(path, backup_dir)
    updated = original.replace(boot_name["match"], boot_name["replacement"])
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
      with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(updated)
        stream.flush()
        os.fsync(stream.fileno())
      os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
      os.replace(temporary, path)
    except BaseException:
      temporary.unlink(missing_ok=True)
      raise


if __name__ == "__main__":
  main()
