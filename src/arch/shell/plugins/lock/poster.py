#!/usr/bin/python3 -I
"""Create and reuse a cached video poster for the lock screen."""

from __future__ import annotations

import fcntl
import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import TextIO, TypedDict, TypeGuard

import yaml


class PosterCache(TypedDict):
  directory: str
  key_prefix: str
  extension: str
  lock_file: str
  temporary_prefix: str
  signature_fields: list[str]
  signature_separator: str
  key_separator: str
  hash_algorithm: str
  obsolete_pattern: str


class PosterLock(TypedDict):
  wait_seconds: int
  poll_interval_seconds: float


class PosterThumbnail(TypedDict):
  generator: str
  size: int
  quality: int
  timeout_seconds: int
  kill_grace_seconds: int


class PosterSettings(TypedDict):
  cache: PosterCache
  lock: PosterLock
  thumbnail: PosterThumbnail


def _is_string_list(value: object) -> TypeGuard[list[str]]:
  return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_poster_settings(value: object) -> TypeGuard[PosterSettings]:
  if not isinstance(value, dict):
    return False
  cache = value.get("cache")
  lock = value.get("lock")
  thumbnail = value.get("thumbnail")
  if not isinstance(cache, dict) or not isinstance(lock, dict) or not isinstance(thumbnail, dict):
    return False
  cache_strings = (
    "directory", "key_prefix", "extension", "lock_file", "temporary_prefix", "signature_separator",
    "key_separator", "hash_algorithm", "obsolete_pattern",
  )
  thumbnail_ints = ("size", "quality", "timeout_seconds", "kill_grace_seconds")
  return (
    all(isinstance(cache.get(key), str) for key in cache_strings)
    and _is_string_list(cache.get("signature_fields"))
    and {"size", "mtime_ns", "ctime_ns"}.issubset(cache["signature_fields"])
    and type(lock.get("wait_seconds")) is int
    and isinstance(lock.get("poll_interval_seconds"), float)
    and isinstance(thumbnail.get("generator"), str)
    and all(type(thumbnail.get(key)) is int for key in thumbnail_ints)
  )


def settings() -> PosterSettings:
  root = Path(os.environ["AP"])
  with (root / "data/shell/lock-poster.yml").open(encoding="utf-8") as stream:
    config: object = yaml.safe_load(stream)
  if not _is_poster_settings(config):
    raise ValueError("invalid lock poster settings")
  return config


def signature(source: Path, config: PosterSettings) -> str:
  stat = source.stat()
  values = {
    "size": stat.st_size,
    "mtime_ns": stat.st_mtime_ns,
    "ctime_ns": stat.st_ctime_ns,
  }
  fields = config["cache"]["signature_fields"]
  return config["cache"]["signature_separator"].join(str(values[field]) for field in fields)


def acquire_lock(lock_file: Path, config: PosterSettings) -> TextIO:
  lock = lock_file.open("a")
  deadline = time.monotonic() + config["lock"]["wait_seconds"]
  while True:
    try:
      fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
      return lock
    except BlockingIOError:
      if time.monotonic() >= deadline:
        lock.close()
        raise TimeoutError
      time.sleep(config["lock"]["poll_interval_seconds"])


def make_poster(source: Path, poster: Path, config: PosterSettings) -> None:
  thumbnail = config["thumbnail"]
  descriptor, temporary_name = tempfile.mkstemp(
    prefix=config["cache"]["temporary_prefix"],
    suffix=config["cache"]["extension"],
    dir=poster.parent,
  )
  os.close(descriptor)
  temporary = Path(temporary_name)
  command = [
    thumbnail["generator"],
    "-i", str(source),
    "-o", str(temporary),
    "-s", str(thumbnail["size"]),
    "-q", str(thumbnail["quality"]),
  ]
  try:
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
      status = process.wait(timeout=thumbnail["timeout_seconds"])
    except subprocess.TimeoutExpired:
      process.terminate()
      try:
        process.wait(timeout=thumbnail["kill_grace_seconds"])
      except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
      raise TimeoutError
    if status != 0 or not temporary.is_file() or temporary.stat().st_size == 0:
      raise subprocess.CalledProcessError(status or 1, command)
    temporary.replace(poster)
  finally:
    temporary.unlink(missing_ok=True)


def main() -> int:
  config = settings()
  if len(sys.argv) < 2:
    return 1
  source = Path(sys.argv[1])
  try:
    source_signature = signature(source, config)
  except OSError:
    return 1

  cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / config["cache"]["directory"]
  cache.mkdir(parents=True, exist_ok=True)
  key_input = config["cache"]["key_separator"].join((str(source), source_signature)).encode()
  key = hashlib.new(config["cache"]["hash_algorithm"], key_input).hexdigest()
  poster = cache / (config["cache"]["key_prefix"] + key + config["cache"]["extension"])

  try:
    lock = acquire_lock(cache / config["cache"]["lock_file"], config)
  except (OSError, TimeoutError):
    return 1
  with lock:
    if not poster.is_file() or poster.stat().st_size == 0:
      try:
        make_poster(source, poster, config)
      except (OSError, subprocess.SubprocessError, TimeoutError):
        return 1
      obsolete = config["cache"]["obsolete_pattern"]
      for old_poster in cache.glob(obsolete):
        if old_poster != poster:
          old_poster.unlink(missing_ok=True)

  print(poster)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
