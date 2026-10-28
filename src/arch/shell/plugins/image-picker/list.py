#!/usr/bin/python3 -I
"""List selectable media and prepare bounded video thumbnails."""

from __future__ import annotations

import concurrent.futures
import fcntl
import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import TypedDict, TypeGuard

import yaml


class SignatureConfig(TypedDict):
  size_separator: str
  fields: list[str]


class CacheConfig(TypedDict):
  directory: str
  index: str
  extension: str
  failure_extension: str
  lock_extension: str
  temporary_suffix: str
  hash_algorithm: str
  signature: SignatureConfig
  row_separator: str
  directory_separator: str
  legacy_still_thumbnail: bool


class DiscoveryConfig(TypedDict):
  maximum_depth: int
  extensions: dict[str, list[str]]


class ConcurrencyConfig(TypedDict):
  cpu_divisor: int
  minimum: int


class ThumbnailConfig(TypedDict):
  generator: str
  size: int
  quality: int
  timeout_seconds: int
  kill_grace_seconds: int
  lock_wait_seconds: int
  stale_lock_seconds: int
  lock_poll_interval_seconds: float
  concurrency: ConcurrencyConfig


class ImagePickerConfig(TypedDict):
  cache: CacheConfig
  discovery: DiscoveryConfig
  thumbnails: ThumbnailConfig


def _is_string_list(value: object) -> TypeGuard[list[str]]:
  return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_string_lists(value: object) -> TypeGuard[dict[str, list[str]]]:
  return isinstance(value, dict) and all(
    isinstance(key, str) and _is_string_list(items) for key, items in value.items()
  )


def _is_image_picker_config(value: object) -> TypeGuard[ImagePickerConfig]:
  if not isinstance(value, dict):
    return False
  cache = value.get("cache")
  discovery = value.get("discovery")
  thumbnails = value.get("thumbnails")
  if not isinstance(cache, dict) or not isinstance(discovery, dict) or not isinstance(thumbnails, dict):
    return False
  signature = cache.get("signature")
  extensions = discovery.get("extensions")
  concurrency = thumbnails.get("concurrency")
  if not isinstance(signature, dict) or not isinstance(extensions, dict) or not isinstance(concurrency, dict):
    return False
  cache_strings = (
    "directory", "index", "extension", "failure_extension", "lock_extension", "temporary_suffix",
    "hash_algorithm", "row_separator", "directory_separator",
  )
  if (
    any(not isinstance(cache.get(key), str) for key in cache_strings)
    or not isinstance(cache.get("legacy_still_thumbnail"), bool)
    or not isinstance(signature.get("size_separator"), str)
    or not _is_string_list(signature.get("fields"))
    or not {"size", "mtime"}.issubset(signature["fields"])
    or type(discovery.get("maximum_depth")) is not int
    or not _is_string_lists(extensions)
    or any(not items for items in extensions.values())
    or not isinstance(thumbnails.get("generator"), str)
    or any(type(thumbnails.get(key)) is not int for key in (
      "size", "quality", "timeout_seconds", "kill_grace_seconds", "lock_wait_seconds", "stale_lock_seconds",
    ))
    or not isinstance(thumbnails.get("lock_poll_interval_seconds"), float)
    or type(concurrency.get("cpu_divisor")) is not int
    or type(concurrency.get("minimum")) is not int
    or concurrency["cpu_divisor"] < 1
    or concurrency["minimum"] < 1
  ):
    return False
  return True


def load_config() -> ImagePickerConfig:
  root = Path(os.environ["AP"])
  config_path = root / "data/shell/image-picker.yml"
  with config_path.open(encoding="utf-8") as stream:
    config: object = yaml.safe_load(stream)
  if not _is_image_picker_config(config):
    raise ValueError("invalid image picker configuration")
  return config


def digest(value: bytes, algorithm: str) -> str:
  return hashlib.new(algorithm, value).hexdigest()


def signature_for(path: Path, config: ImagePickerConfig) -> str:
  stat = path.stat()
  values = {"size": str(stat.st_size), "mtime": str(int(stat.st_mtime))}
  signature = config["cache"]["signature"]
  return signature["size_separator"].join(values[name] for name in signature["fields"])


def is_video(path: Path, config: ImagePickerConfig) -> bool:
  return path.suffix.casefold().lstrip(".") in config["discovery"]["extensions"]["videos"]


def discover(directories: str, config: ImagePickerConfig) -> list[Path]:
  extensions = {
    extension.casefold()
    for group in config["discovery"]["extensions"].values()
    for extension in group
  }
  found = []
  for directory in directories.split(config["cache"]["directory_separator"]):
    if not directory:
      continue
    pending_directories = [(Path(directory), 0)]
    while pending_directories:
      current, depth = pending_directories.pop()
      try:
        with os.scandir(current) as entries:
          for entry in entries:
            try:
              if entry.is_file(follow_symlinks=True):
                if Path(entry.name).suffix.casefold().lstrip(".") in extensions:
                  found.append(Path(entry.path))
              elif depth + 1 < config["discovery"]["maximum_depth"] and entry.is_dir(follow_symlinks=True):
                pending_directories.append((Path(entry.path), depth + 1))
            except OSError:
              continue
      except OSError:
        continue
  return sorted(found, key=os.fsencode)


def cache_paths(cache_dir: Path, image: Path, config: ImagePickerConfig) -> tuple[Path, str]:
  signature = signature_for(image, config)
  index_file = cache_dir / config["cache"]["index"]
  separator = config["cache"]["row_separator"]
  try:
    with index_file.open(encoding="utf-8", errors="replace") as stream:
      for line in stream:
        fields = line.rstrip("\n").split(separator)
        if len(fields) >= 3 and fields[0] == str(image) and fields[1] == signature:
          return cache_dir / (fields[2] + config["cache"]["extension"]), signature
  except OSError:
    pass
  key = digest((str(image) + separator + signature).encode(), config["cache"]["hash_algorithm"])
  return cache_dir / (key + config["cache"]["extension"]), signature


def make_video_thumbnail(image: Path, thumbnail: Path, config: ImagePickerConfig) -> None:
  options = config["thumbnails"]
  lock_path = Path(str(thumbnail) + config["cache"]["lock_extension"])
  try:
    if lock_path.is_dir() and time.time() - lock_path.stat().st_mtime > options["stale_lock_seconds"]:
      lock_path.rmdir()
  except OSError:
    pass

  try:
    lock_stream = lock_path.open("a")
  except OSError:
    return

  with lock_stream:
    deadline = time.monotonic() + options["lock_wait_seconds"]
    while True:
      try:
        fcntl.flock(lock_stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        break
      except BlockingIOError:
        if time.monotonic() >= deadline:
          return
        time.sleep(options["lock_poll_interval_seconds"])

    for stale in thumbnail.parent.glob(thumbnail.name + ".*.jpg"):
      try:
        stale.unlink()
      except OSError:
        pass
    if thumbnail.is_file():
      return

    descriptor, temp_name = tempfile.mkstemp(
      prefix=thumbnail.name + ".", suffix=config["cache"]["temporary_suffix"], dir=thumbnail.parent
    )
    os.close(descriptor)
    temporary = Path(temp_name)
    command = [
      options["generator"], "-i", str(image), "-o", str(temporary),
      "-s", str(options["size"]), "-q", str(options["quality"]),
    ]
    try:
      process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      try:
        status = process.wait(timeout=options["timeout_seconds"])
      except subprocess.TimeoutExpired:
        process.terminate()
        try:
          process.wait(timeout=options["kill_grace_seconds"])
        except subprocess.TimeoutExpired:
          process.kill()
          process.wait()
        status = 124 if process.returncode != -9 else 137

      if status == 0:
        temporary.replace(thumbnail)
      else:
        temporary.unlink(missing_ok=True)
        thumbnail.unlink(missing_ok=True)
        if status not in (124, 137):
          Path(str(thumbnail) + config["cache"]["failure_extension"]).touch()
    except OSError:
      temporary.unlink(missing_ok=True)
      Path(str(thumbnail) + config["cache"]["failure_extension"]).touch()


def thumbnail_for(image: Path, cache_dir: Path, config: ImagePickerConfig) -> Path | None:
  try:
    thumbnail, _signature = cache_paths(cache_dir, image, config)
  except OSError:
    return None

  if not thumbnail.is_file() and not is_video(image, config) and config["cache"]["legacy_still_thumbnail"]:
    try:
      legacy = digest(image.read_bytes(), config["cache"]["hash_algorithm"])
      legacy_thumbnail = cache_dir / (legacy + config["cache"]["extension"])
      if legacy_thumbnail.is_file():
        thumbnail = legacy_thumbnail
    except OSError:
      pass

  if thumbnail.is_file():
    return thumbnail
  return None if is_video(image, config) else image


def main() -> int:
  config = load_config()
  cache_dir = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / config["cache"]["directory"]
  cache_dir.mkdir(parents=True, exist_ok=True)
  images = discover(sys.argv[1] if len(sys.argv) > 1 else "", config)

  pending = []
  for image in images:
    if not is_video(image, config):
      continue
    try:
      thumbnail, _signature = cache_paths(cache_dir, image, config)
    except OSError:
      continue
    failed = Path(str(thumbnail) + config["cache"]["failure_extension"])
    if not thumbnail.is_file() and not failed.exists():
      pending.append((image, thumbnail))

  cpu_divisor = config["thumbnails"]["concurrency"]["cpu_divisor"]
  minimum = config["thumbnails"]["concurrency"]["minimum"]
  workers = max(minimum, (os.cpu_count() or minimum) // cpu_divisor)
  with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
    futures = [executor.submit(make_video_thumbnail, image, thumb, config) for image, thumb in pending]
    for future in futures:
      future.result()

  for image in images:
    thumbnail = thumbnail_for(image, cache_dir, config)
    if thumbnail is not None:
      print(f"{image}\t{thumbnail}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
