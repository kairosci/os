from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml


def _settings() -> dict[str, Any]:
  ap = Path(os.environ["ARCH_PATH"])
  with (ap / "data/installer/config-setup.yml").open(encoding="utf-8") as stream:
    settings = yaml.safe_load(stream)
  if not isinstance(settings, dict):
    raise ValueError("invalid system setup settings")
  return settings["systemd_boot_snapshots"]


def _copy_plugin(source: Path, target: Path, mode: str, directory_mode: str) -> None:
  target.parent.mkdir(mode=int(directory_mode, 8), parents=True, exist_ok=True)
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as stream, source.open("rb") as plugin:
      shutil.copyfileobj(plugin, stream)
      stream.flush()
      os.fsync(stream.fileno())
    os.chmod(temporary, int(mode, 8))
    os.replace(temporary, target)
    directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def _disable_legacy_plugin(path: Path) -> None:
  try:
    plugin_stat = path.lstat()
  except FileNotFoundError:
    return
  if stat.S_ISREG(plugin_stat.st_mode):
    os.chmod(path, stat.S_IMODE(plugin_stat.st_mode) & ~0o111, follow_symlinks=False)


def _run_optional(command: list[str]) -> None:
  subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
  settings = _settings()
  ap = Path(os.environ["ARCH_PATH"])
  helper = subprocess.run([str(ap / settings["helper"])], check=False)
  boot_entry = settings["boot_entry"]
  esp = os.environ.get(boot_entry["environment_override"], boot_entry["default_esp"])
  if helper.returncode or not (Path(esp) / boot_entry["relative_path"]).is_file():
    return

  plugin = settings["plugin"]
  target = plugin["target"]
  if os.geteuid() != 0:
    target = os.environ.get(plugin["target_environment"], target)
  _copy_plugin(
    ap / plugin["source"],
    Path(target),
    plugin["mode"],
    plugin["directory_mode"],
  )
  settings_target = Path(target).with_name(Path(target).name + plugin["settings_suffix"])
  _copy_plugin(
    ap / plugin["settings_source"],
    settings_target,
    plugin["settings_mode"],
    plugin["directory_mode"],
  )
  _run_optional(settings["disable_units"])
  _disable_legacy_plugin(Path(settings["legacy_plugin"]["path"]))
  for value in settings["remove_files"]:
    path = Path(value)
    if path.is_file() or path.is_symlink():
      path.unlink()
  subprocess.run(settings["reload_units"], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
  main()
