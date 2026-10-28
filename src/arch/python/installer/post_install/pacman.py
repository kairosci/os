"""Restore pacman defaults and initialize platform keyrings after installation."""

from __future__ import annotations

import grp
import os
import pwd
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Literal, TypedDict

import yaml


class Messages(TypedDict):
  invalid_platform: str
  untrusted_image_directory: str
  untrusted_image_manifest: str
  invalid_image_manifest: str
  unsafe_keyring_request: str
  unsafe_cups_file: str
  image_root_required: str


class ImageSettings(TypedDict):
  root_environment: str
  directory: str
  manifest: str
  keyring_request: str
  required_format: str
  mode: str


class CupsSettings(TypedDict):
  source: str
  target: str
  pacnew: str
  mode: str
  owner: str
  group: str


class PacmanSettings(TypedDict):
  platform_command: list[str]
  template_directories: dict[str, str]
  default_channels: dict[str, str]
  channels: list[str]
  alarm_keyring_platforms: list[str]
  alarm_keyring_package: str
  package_command: list[str]
  keyring_command: list[str]
  apply_command: str
  repositories_script: str
  image: ImageSettings
  cups: CupsSettings
  python_command: list[str]
  trusted_path: str
  messages: dict[str, Messages]


MessageKey = Literal[
  "invalid_platform", "untrusted_image_directory", "untrusted_image_manifest",
  "invalid_image_manifest", "unsafe_keyring_request", "unsafe_cups_file", "image_root_required",
]


def _mapping(value: object, label: str) -> dict[object, object]:
  if not isinstance(value, dict):
    raise TypeError(f"invalid post-install pacman settings: {label} must be a mapping")
  return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
  if not isinstance(value, str):
    raise TypeError(f"invalid post-install pacman settings: {label} must be a string")
  return value


def _text_list(value: object, label: str) -> list[str]:
  if not isinstance(value, list) or not value:
    raise TypeError(f"invalid post-install pacman settings: {label} must be a non-empty list")
  return [_text(item, f"{label} item") for item in value]


def _text_mapping(value: object, label: str) -> dict[str, str]:
  raw = _mapping(value, label)
  return {_text(key, f"{label} key"): _text(item, f"{label} value") for key, item in raw.items()}


def _messages(value: object) -> dict[str, Messages]:
  raw = _mapping(value, "messages")
  result: dict[str, Messages] = {}
  for language, raw_messages in raw.items():
    key = _text(language, "messages language")
    messages = _mapping(raw_messages, f"messages.{key}")
    result[key] = {
      "invalid_platform": _text(messages.get("invalid_platform"), f"messages.{key}.invalid_platform"),
      "untrusted_image_directory": _text(messages.get("untrusted_image_directory"), f"messages.{key}.untrusted_image_directory"),
      "untrusted_image_manifest": _text(messages.get("untrusted_image_manifest"), f"messages.{key}.untrusted_image_manifest"),
      "invalid_image_manifest": _text(messages.get("invalid_image_manifest"), f"messages.{key}.invalid_image_manifest"),
      "unsafe_keyring_request": _text(messages.get("unsafe_keyring_request"), f"messages.{key}.unsafe_keyring_request"),
      "unsafe_cups_file": _text(messages.get("unsafe_cups_file"), f"messages.{key}.unsafe_cups_file"),
      "image_root_required": _text(messages.get("image_root_required"), f"messages.{key}.image_root_required"),
    }
  if "en" not in result:
    raise ValueError("invalid post-install pacman settings: English messages are required")
  return result


def _mode(value: object, label: str) -> str:
  mode = _text(value, label)
  try:
    parsed = int(mode, 8)
  except ValueError as error:
    raise ValueError(f"invalid post-install pacman settings: {label} must be an octal mode") from error
  if not 0 <= parsed <= 0o7777:
    raise ValueError(f"invalid post-install pacman settings: {label} is outside the supported mode range")
  return mode


def settings() -> tuple[Path, PacmanSettings]:
  ap = Path(os.environ["ARCH_PATH"])
  path = ap / "data/installer/post-install.yml"
  raw: object = yaml.safe_load(path.read_text(encoding="utf-8"))
  root = _mapping(raw, "root")
  config = _mapping(root.get("pacman"), "pacman")
  image = _mapping(config.get("image"), "image")
  cups = _mapping(config.get("cups"), "cups")
  return ap, {
    "platform_command": _text_list(config.get("platform_command"), "platform_command"),
    "template_directories": _text_mapping(config.get("template_directories"), "template_directories"),
    "default_channels": _text_mapping(config.get("default_channels"), "default_channels"),
    "channels": _text_list(config.get("channels"), "channels"),
    "alarm_keyring_platforms": _text_list(config.get("alarm_keyring_platforms"), "alarm_keyring_platforms"),
    "alarm_keyring_package": _text(config.get("alarm_keyring_package"), "alarm_keyring_package"),
    "package_command": _text_list(config.get("package_command"), "package_command"),
    "keyring_command": _text_list(config.get("keyring_command"), "keyring_command"),
    "apply_command": _text(config.get("apply_command"), "apply_command"),
    "repositories_script": _text(config.get("repositories_script"), "repositories_script"),
    "image": {
      "root_environment": _text(image.get("root_environment"), "image.root_environment"),
      "directory": _text(image.get("directory"), "image.directory"),
      "manifest": _text(image.get("manifest"), "image.manifest"),
      "keyring_request": _text(image.get("keyring_request"), "image.keyring_request"),
      "required_format": _text(image.get("required_format"), "image.required_format"),
      "mode": _mode(image.get("mode"), "image.mode"),
    },
    "cups": {
      "source": _text(cups.get("source"), "cups.source"),
      "target": _text(cups.get("target"), "cups.target"),
      "pacnew": _text(cups.get("pacnew"), "cups.pacnew"),
      "mode": _mode(cups.get("mode"), "cups.mode"),
      "owner": _text(cups.get("owner"), "cups.owner"),
      "group": _text(cups.get("group"), "cups.group"),
    },
    "python_command": _text_list(config.get("python_command"), "python_command"),
    "trusted_path": _text(config.get("trusted_path"), "trusted_path"),
    "messages": _messages(config.get("messages")),
  }


def message(config: PacmanSettings, key: MessageKey, **values: str) -> str:
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


def image_root(config: PacmanSettings) -> Path:
  if os.geteuid() == 0:
    return Path("/")
  environment = config["image"]["root_environment"]
  root = os.environ.get(environment)
  if root is None or root == "":
    raise PermissionError(message(config, "image_root_required"))
  return Path(root)


def image_manifest(root: Path, config: PacmanSettings) -> Path | None:
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


def request_image_keyring(root: Path, config: PacmanSettings) -> None:
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


def install_cups_policy(ap: Path, config: PacmanSettings) -> None:
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


def _main() -> int:
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


def main() -> int:
  try:
    return _main()
  except (UnicodeError, TypeError, ValueError, yaml.YAMLError) as error:
    print(f"Invalid post-install pacman configuration: {error}", file=sys.stderr)
    return os.EX_CONFIG
  except subprocess.CalledProcessError as error:
    print(f"Post-install pacman command failed: {error}", file=sys.stderr)
    return error.returncode
  except (OSError, subprocess.SubprocessError) as error:
    print(f"Could not complete post-install pacman setup: {error}", file=sys.stderr)
    return os.EX_SOFTWARE


if __name__ == "__main__":
  raise SystemExit(main())
