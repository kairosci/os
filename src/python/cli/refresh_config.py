from __future__ import annotations

import os
import secrets
import stat
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class ConfigNotShipped(Exception):
  pass


class UnsafeConfigPath(ValueError):
  pass


def _message(key: str, *arguments: str) -> str:
  arch_path = Path(os.environ["ARCH_PATH"])
  command = [str(arch_path / "src/cli/arch-i18n"), key, *arguments]
  result = subprocess.run(command, check=False, capture_output=True, text=True)
  if result.returncode:
    return key
  return result.stdout


def _inside(path: Path, root: Path) -> bool:
  return path == root or root in path.parents


def _write_private(path: Path, content: bytes, mode: int) -> None:
  descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
  try:
    with os.fdopen(descriptor, "wb") as stream:
      stream.write(content)
      stream.flush()
      os.fsync(stream.fileno())
  except BaseException:
    path.unlink(missing_ok=True)
    raise


def _backup_path(path: Path, files: dict[str, Any]) -> Path:
  timestamp = datetime.now().astimezone().strftime(files["backup_timestamp_format"])
  suffix = f'{files["backup_suffix"]}{timestamp}'
  candidate = path.with_name(path.name + suffix)
  if not candidate.exists() and not candidate.is_symlink():
    return candidate

  while True:
    candidate = path.with_name(path.name + suffix + "." + secrets.token_hex(4))
    if not candidate.exists() and not candidate.is_symlink():
      return candidate


def _destination_parent(root: Path, components: tuple[str, ...], directory_mode: str) -> Path:
  current = root
  for component in components:
    current = current / component
    try:
      current.mkdir(mode=int(directory_mode, 8))
    except FileExistsError:
      pass
    resolved = current.resolve(strict=True)
    if not _inside(resolved, root) or not resolved.is_dir():
      raise UnsafeConfigPath("unsafe destination parent")
    current = resolved
  return current


def _refresh(relative_path: str) -> tuple[Path, Path | None, bool]:
  arch_path = Path(os.environ["ARCH_PATH"]).resolve(strict=True)
  with (arch_path / "data/cli/refresh-config.yml").open(encoding="utf-8") as stream:
    settings = yaml.safe_load(stream)

  raw_components = relative_path.split("/")
  components = tuple(Path(relative_path).parts)
  forbidden = set(settings["paths"]["forbidden_components"])
  if (
    not relative_path
    or Path(relative_path).is_absolute()
    or any(component in forbidden for component in raw_components)
    or not components
  ):
    raise UnsafeConfigPath("invalid relative path")

  source_root = (arch_path / settings["paths"]["source_directory"]).resolve(strict=True)
  if not _inside(source_root, arch_path):
    raise UnsafeConfigPath("source root leaves Arch path")
  source_candidate = source_root.joinpath(*components)
  try:
    source = source_candidate.resolve(strict=True)
  except FileNotFoundError:
    raise ConfigNotShipped(relative_path) from None
  if not _inside(source, source_root):
    raise UnsafeConfigPath("source symlink leaves its root")
  if not source.is_file():
    raise ConfigNotShipped(relative_path)

  home = Path(os.environ["HOME"]).resolve(strict=True)
  config_home_value = os.environ.get("XDG_CONFIG_HOME")
  config_home = Path(config_home_value) if config_home_value else home / settings["paths"]["user_directory"]
  if not config_home.is_absolute():
    raise UnsafeConfigPath("invalid config root")
  config_home.mkdir(mode=int(settings["paths"]["directory_mode"], 8), parents=True, exist_ok=True)
  user_root = config_home.resolve(strict=True)
  if not user_root.is_dir():
    raise UnsafeConfigPath("invalid config root")

  parent = _destination_parent(user_root, components[:-1], settings["paths"]["directory_mode"])
  destination_entry = parent / components[-1]
  if destination_entry.is_symlink():
    try:
      destination = destination_entry.resolve(strict=True)
    except FileNotFoundError:
      raise UnsafeConfigPath("dangling destination symlink") from None
    if not _inside(destination, user_root) or not destination.is_file():
      raise UnsafeConfigPath("unsafe destination symlink")
  elif destination_entry.exists():
    destination = destination_entry.resolve(strict=True)
    if not _inside(destination, user_root) or not destination.is_file():
      raise UnsafeConfigPath("unsafe destination file")
  else:
    destination = destination_entry

  source_content = source.read_bytes()
  previous_content: bytes | None = None
  previous_mode: int | None = None
  if destination.exists():
    if destination.is_symlink() or not destination.is_file():
      raise UnsafeConfigPath("unsafe destination file")
    previous_content = destination.read_bytes()
    previous_mode = stat.S_IMODE(destination.stat().st_mode)
    if previous_content == source_content:
      return destination, None, False

  file_settings = settings["files"]
  descriptor, temporary_name = tempfile.mkstemp(
    prefix=f'{file_settings["temporary_prefix"]}{destination.name}.',
    dir=destination.parent,
  )
  temporary = Path(temporary_name)
  try:
    final_mode = previous_mode if previous_mode is not None else stat.S_IMODE(source.stat().st_mode)
    os.fchmod(descriptor, int(file_settings["temporary_mode"], 8))
    with os.fdopen(descriptor, "wb") as stream:
      stream.write(source_content)
      stream.flush()
      os.fsync(stream.fileno())
      os.fchmod(stream.fileno(), final_mode)
      os.fsync(stream.fileno())

    backup: Path | None = None
    if previous_content is not None:
      backup = _backup_path(destination, file_settings)
      _write_private(backup, previous_content, int(file_settings["backup_mode"], 8))
    os.replace(temporary, destination)
    directory = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
      os.fsync(directory)
    finally:
      os.close(directory)
    return destination, backup, True
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise


def main() -> int:
  if len(sys.argv) != 2:
    print(_message("refreshConfig.usage"), file=sys.stderr)
    return 1

  relative_path = sys.argv[1]
  try:
    destination, backup, changed = _refresh(relative_path)
  except ConfigNotShipped:
    print(_message("refreshConfig.notShipped", relative_path), file=sys.stderr)
    return 1
  except UnsafeConfigPath:
    print(_message("refreshConfig.unsafePath", relative_path), file=sys.stderr)
    return 1
  except (OSError, RuntimeError, yaml.YAMLError) as error:
    print(_message("refreshConfig.failed", relative_path, str(error)), file=sys.stderr)
    return 1

  if changed and backup:
    print(_message("refreshConfig.replaced", str(destination)))
    print(_message("refreshConfig.backup", str(backup)))
    print(_message("refreshConfig.changes"))
    subprocess.run(["diff", "--", str(destination), str(backup)], check=False)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
