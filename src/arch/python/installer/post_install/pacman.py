"""Restore pacman defaults and initialize platform keyrings after installation."""

from __future__ import annotations

import grp
import os
from pathlib import Path
import pwd
import shutil
import stat
import subprocess
import tempfile
from typing import Any

import yaml


def settings() -> tuple[Path, dict[str, Any]]:
  ap = Path(os.environ["ARCH_PATH"])
  path = ap / "data/installer/post-install.yml"
  config = yaml.safe_load(path.read_text(encoding="utf-8"))
  if not isinstance(config, dict) or not isinstance(config.get("pacman"), dict):
    raise ValueError("invalid post-install pacman settings")
  return ap, config["pacman"]


def message(config: dict[str, Any], key: str, **values: str) -> str:
  language = os.environ.get("LANG", "en").split(".", 1)[0].split("_", 1)[0].lower()
  messages = config["messages"]
  return messages.get(language, messages["en"])[key].format(**values)


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
  return subprocess.run(command, check=True, capture_output=capture, text=True)


def _safe_owner_mode(path: Path, owner: int) -> bool:
  try:
    metadata = path.lstat()
  except FileNotFoundError:
    return False
  return stat.S_ISDIR(metadata.st_mode) and metadata.st_uid == owner and stat.S_IMODE(metadata.st_mode) & 0o022 == 0


def _safe_regular_file(path: Path, owner: int) -> bool:
  try:
    metadata = path.lstat()
  except FileNotFoundError:
    return False
  return stat.S_ISREG(metadata.st_mode) and metadata.st_uid == owner and stat.S_IMODE(metadata.st_mode) & 0o022 == 0


def image_root(config: dict[str, Any]) -> Path:
  if os.geteuid() == 0:
    return Path("/")
  environment = config["image"]["root_environment"]
  root = os.environ.get(environment)
  if not root:
    raise PermissionError(message(config, "image_root_required"))
  return Path(root)


def image_manifest(root: Path, config: dict[str, Any]) -> Path | None:
  image = config["image"]
  directory = root / image["directory"]
  manifest = directory / image["manifest"]
  owner = os.geteuid()
  if not directory.exists() and not directory.is_symlink():
    if manifest.exists() or manifest.is_symlink():
      raise PermissionError(message(config, "untrusted_image_directory", path=str(directory)))
    return None
  if not _safe_owner_mode(directory, owner):
    raise PermissionError(message(config, "untrusted_image_directory", path=str(directory)))
  if not manifest.exists() and not manifest.is_symlink():
    return None
  if not _safe_regular_file(manifest, owner):
    raise PermissionError(message(config, "untrusted_image_manifest", path=str(manifest)))
  lines = manifest.read_text(encoding="utf-8").splitlines()
  if f"format={image['required_format']}" not in lines:
    raise ValueError(message(config, "invalid_image_manifest", path=str(manifest)))
  return manifest


def request_image_keyring(root: Path, config: dict[str, Any]) -> None:
  image = config["image"]
  path = root / image["directory"] / image["keyring_request"]
  owner = os.geteuid()
  flags = os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW
  try:
    metadata = path.lstat()
  except FileNotFoundError:
    descriptor = os.open(path, flags | os.O_CREAT | os.O_EXCL, int(image["mode"], 8))
  else:
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != owner or stat.S_IMODE(metadata.st_mode) & 0o022:
      raise ValueError(message(config, "unsafe_keyring_request", path=str(path)))
    descriptor = os.open(path, flags, int(image["mode"], 8))
    opened = os.fstat(descriptor)
    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
      os.close(descriptor)
      raise ValueError(message(config, "unsafe_keyring_request", path=str(path)))
    os.ftruncate(descriptor, 0)
  with os.fdopen(descriptor, "wb") as request:
    os.fchmod(request.fileno(), int(image["mode"], 8))
    request.flush()
    os.fsync(request.fileno())


def install_cups_policy(ap: Path, config: dict[str, Any]) -> None:
  cups = config["cups"]
  source = ap / cups["source"]
  target = Path(cups["target"])
  try:
    source_mode = source.lstat().st_mode
    target_mode = target.lstat().st_mode
  except FileNotFoundError:
    return
  if not stat.S_ISREG(source_mode) or not stat.S_ISREG(target_mode):
    raise ValueError(message(config, "unsafe_cups_file", path=str(target)))

  group_id = grp.getgrnam(cups["group"]).gr_gid
  owner_id = pwd.getpwnam(cups["owner"]).pw_uid
  descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
  temporary = Path(temporary_name)
  try:
    with os.fdopen(descriptor, "wb") as destination, source.open("rb") as policy:
      shutil.copyfileobj(policy, destination)
      os.fchmod(destination.fileno(), int(cups["mode"], 8))
      os.fchown(destination.fileno(), owner_id, group_id)
      destination.flush()
      os.fsync(destination.fileno())
    os.replace(temporary, target)
    directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)
  except BaseException:
    temporary.unlink(missing_ok=True)
    raise

  pacnew = Path(cups["pacnew"])
  if pacnew.is_file() or pacnew.is_symlink():
    pacnew.unlink()


def main() -> int:
  ap, config = settings()
  if os.geteuid() == 0:
    os.environ["PATH"] = config["trusted_path"]

  platform_result = run(config["platform_command"], capture=True)
  platform = platform_result.stdout.strip()
  template_directory = config["template_directories"].get(platform)
  default_channel = config["default_channels"].get(platform)
  if template_directory is None or default_channel is None:
    raise ValueError(message(config, "invalid_platform", platform=platform))

  templates = ap / template_directory
  channel = os.environ.get("ARCH_MIRROR", "")
  if channel not in config["channels"] or not all(
    (templates / filename.format(channel=channel)).is_file()
    for filename in ("pacman-{channel}.conf", "mirrorlist-{channel}")
  ):
    channel = default_channel

  needs_alarm_keyring = platform in config["alarm_keyring_platforms"]
  if needs_alarm_keyring:
    run([*config["package_command"], config["alarm_keyring_package"]])

  root = image_root(config)
  manifest = image_manifest(root, config) if needs_alarm_keyring else None
  target_root = str(root) if os.geteuid() != 0 else "/"
  run([config["apply_command"].format(arch_path=str(ap)), channel, target_root])

  if needs_alarm_keyring:
    if manifest is not None:
      request_image_keyring(root, config)
    else:
      run([*config["keyring_command"], "--init"])
      run([*config["keyring_command"], "--populate"])

  install_cups_policy(ap, config)
  run([*config["python_command"], str(ap / config["repositories_script"])])
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
