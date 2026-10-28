from __future__ import annotations

import os
import pwd
import re
import secrets
import stat
import sys
from pathlib import Path
from typing import TypedDict, TypeGuard

import yaml


class SddmPaths(TypedDict):
  pam_directory: str
  pam_file: str
  temporary_prefix: str


class SddmPolicy(TypedDict):
  create_mode: str
  maximum_parent_mode: str
  required_owner: str
  require_single_link: bool
  patterns: list[str]


class SddmConfig(TypedDict):
  paths: SddmPaths
  limits: dict[str, int]
  file: SddmPolicy
  messages: dict[str, dict[str, str]]
  default_language: str


def _is_string_mapping(value: object) -> TypeGuard[dict[str, str]]:
  return isinstance(value, dict) and all(
    isinstance(key, str) and isinstance(item, str) for key, item in value.items()
  )


def _is_sddm_config(value: object) -> TypeGuard[SddmConfig]:
  if not isinstance(value, dict):
    return False
  paths = value.get("paths")
  policy = value.get("file")
  limits = value.get("limits")
  messages = value.get("messages")
  return (
    isinstance(paths, dict)
    and all(isinstance(paths.get(key), str) for key in ("pam_directory", "pam_file", "temporary_prefix"))
    and isinstance(policy, dict)
    and all(isinstance(policy.get(key), str) for key in ("create_mode", "maximum_parent_mode", "required_owner"))
    and isinstance(policy.get("require_single_link"), bool)
    and isinstance(policy.get("patterns"), list)
    and all(isinstance(pattern, str) for pattern in policy["patterns"])
    and isinstance(limits, dict)
    and type(limits.get("maximum_bytes")) is int
    and isinstance(messages, dict)
    and all(isinstance(language, str) and _is_string_mapping(catalog) for language, catalog in messages.items())
    and isinstance(messages.get("en"), dict)
    and isinstance(value.get("default_language"), str)
  )


def load_config() -> SddmConfig:
  root = Path(os.environ["ARCH_PATH"])
  config: object = yaml.safe_load((root / "data/installer/login.yml").read_text(encoding="utf-8"))
  if not _is_sddm_config(config):
    raise ValueError("invalid configuration")
  return config


def message(config: SddmConfig, key: str) -> str:
  locale = os.environ.get("LANG", config["default_language"]).split(".", 1)[0].split("_", 1)[0]
  translations = config["messages"]
  language = locale if locale in translations else config["default_language"]
  return translations[language][key]


def update(config: SddmConfig) -> None:
  paths = config["paths"]
  policy = config["file"]
  directory = paths["pam_directory"]
  owner = pwd.getpwnam(policy["required_owner"]).pw_uid
  writable_mode = int(policy["maximum_parent_mode"], 8)
  create_mode = int(policy["create_mode"], 8)
  flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
  directory_fd = os.open(directory, flags)
  temporary_name = paths["temporary_prefix"] + secrets.token_hex(16)
  try:
    directory_stat = os.fstat(directory_fd)
    if (
      not stat.S_ISDIR(directory_stat.st_mode)
      or directory_stat.st_uid != owner
      or directory_stat.st_mode & writable_mode
    ):
      raise PermissionError("unsafe directory")

    file_flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    try:
      source_fd = os.open(paths["pam_file"], file_flags, dir_fd=directory_fd)
    except FileNotFoundError:
      return

    with os.fdopen(source_fd, "rb") as source:
      metadata = os.fstat(source.fileno())
      if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != owner
        or (policy["require_single_link"] and metadata.st_nlink != 1)
        or metadata.st_mode & writable_mode
      ):
        raise PermissionError("unsafe file")
      if metadata.st_size > config["limits"]["maximum_bytes"]:
        raise ValueError("file too large")
      content = source.read(config["limits"]["maximum_bytes"] + 1)
      if len(content) > config["limits"]["maximum_bytes"]:
        raise ValueError("file too large")

    patterns = [re.compile(pattern.encode()) for pattern in policy["patterns"]]
    lines = content.splitlines(keepends=True)
    filtered = [line for line in lines if not any(pattern.search(line) for pattern in patterns)]
    if filtered == lines:
      return

    temporary_fd = os.open(
      temporary_name,
      os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0),
      create_mode,
      dir_fd=directory_fd,
    )
    try:
      with os.fdopen(temporary_fd, "wb") as temporary:
        temporary.write(b"".join(filtered))
        temporary.flush()
        os.fchown(temporary.fileno(), metadata.st_uid, metadata.st_gid)
        os.fchmod(temporary.fileno(), stat.S_IMODE(metadata.st_mode))
        os.fsync(temporary.fileno())
      os.replace(temporary_name, paths["pam_file"], src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
      os.fsync(directory_fd)
    finally:
      try:
        os.unlink(temporary_name, dir_fd=directory_fd)
      except FileNotFoundError:
        pass
  finally:
    os.close(directory_fd)


def main() -> int:
  config = load_config()
  try:
    update(config)
    return 0
  except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as error:
    key = {
      "unsafe directory": "unsafe_directory",
      "unsafe file": "unsafe_file",
      "file too large": "file_too_large",
    }.get(str(error), "update_failed")
    print(message(config, key), file=sys.stderr)
    return 1


if __name__ == "__main__":
  raise SystemExit(main())
