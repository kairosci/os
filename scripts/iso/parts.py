"""Split and reassemble ISO release assets within GitHub's asset size limit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import TypedDict, cast


MAX_PART_BYTES = 1_900_000_000
READ_SIZE = 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
ISO_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\.iso\Z")


class PartRecord(TypedDict):
  name: str
  size: int
  sha256: str


class Manifest(TypedDict):
  format: int
  iso: str
  size: int
  sha256: str
  part_size: int
  parts: list[PartRecord]


def _regular_file(path: Path, description: str) -> os.stat_result:
  try:
    metadata = path.lstat()
  except FileNotFoundError as error:
    raise ValueError(f"{description} does not exist: {path}") from error
  if not stat.S_ISREG(metadata.st_mode):
    raise ValueError(f"{description} must be a regular file: {path}")
  return metadata


def _write_json(path: Path, value: Manifest) -> None:
  with tempfile.NamedTemporaryFile(
    mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False,
  ) as temporary:
    temporary_path = Path(temporary.name)
    try:
      json.dump(value, temporary, indent=2, sort_keys=True)
      temporary.write("\n")
      temporary.flush()
      os.fsync(temporary.fileno())
      os.replace(temporary_path, path)
    finally:
      temporary_path.unlink(missing_ok=True)


def split_iso(source: Path, output_dir: Path, part_size: int = MAX_PART_BYTES) -> Path:
  metadata = _regular_file(source, "ISO image")
  if not ISO_NAME_PATTERN.fullmatch(source.name) or ".." in source.name:
    raise ValueError("ISO image filename must be a simple .iso filename")
  if not 1 <= part_size <= MAX_PART_BYTES:
    raise ValueError(f"part size must be between 1 and {MAX_PART_BYTES} bytes")
  if metadata.st_size <= 0:
    raise ValueError("ISO image is empty")

  output_dir.mkdir(parents=True, exist_ok=True)
  manifest_path = output_dir / f"{source.name}.parts.json"
  part_count = (metadata.st_size + part_size - 1) // part_size
  part_paths = [output_dir / f"{source.name}.part{index:04d}" for index in range(1, part_count + 1)]
  conflicts = [path.name for path in [manifest_path, *part_paths] if path.exists() or path.is_symlink()]
  if conflicts:
    raise FileExistsError(f"refusing to overwrite existing release assets: {', '.join(conflicts)}")

  whole_digest = hashlib.sha256()
  parts: list[PartRecord] = []
  created: list[Path] = []
  processed = 0
  try:
    with source.open("rb") as input_stream:
      for part_path in part_paths:
        remaining = min(part_size, metadata.st_size - processed)
        part_digest = hashlib.sha256()
        written = 0
        with tempfile.NamedTemporaryFile(dir=output_dir, prefix=f".{part_path.name}.", delete=False) as temporary:
          temporary_path = Path(temporary.name)
          created.append(temporary_path)
          while remaining:
            block = input_stream.read(min(READ_SIZE, remaining))
            if not block:
              raise ValueError("ISO image changed or ended while it was being split")
            temporary.write(block)
            part_digest.update(block)
            whole_digest.update(block)
            written += len(block)
            remaining -= len(block)
            processed += len(block)
          temporary.flush()
          os.fsync(temporary.fileno())
        os.replace(temporary_path, part_path)
        created.remove(temporary_path)
        created.append(part_path)
        parts.append({
          "name": part_path.name,
          "size": written,
          "sha256": part_digest.hexdigest(),
        })

      if input_stream.read(1):
        raise ValueError("ISO image grew while it was being split")

    manifest: Manifest = {
      "format": 1,
      "iso": source.name,
      "size": metadata.st_size,
      "sha256": whole_digest.hexdigest(),
      "part_size": part_size,
      "parts": parts,
    }
    created.append(manifest_path)
    _write_json(manifest_path, manifest)
    created.remove(manifest_path)
    return manifest_path
  except BaseException:
    for path in created:
      path.unlink(missing_ok=True)
    raise


def read_manifest(path: Path) -> Manifest:
  _regular_file(path, "parts manifest")
  try:
    manifest = json.loads(path.read_text(encoding="utf-8"))
  except (UnicodeDecodeError, json.JSONDecodeError) as error:
    raise ValueError(f"invalid parts manifest: {path}") from error
  if not isinstance(manifest, dict) or set(manifest) != {"format", "iso", "size", "sha256", "part_size", "parts"}:
    raise ValueError("parts manifest has an unsupported schema")
  if type(manifest["format"]) is not int or manifest["format"] != 1:
    raise ValueError("parts manifest has an unsupported format version")
  iso_name = manifest["iso"]
  if not isinstance(iso_name, str) or not ISO_NAME_PATTERN.fullmatch(iso_name) or ".." in iso_name:
    raise ValueError("parts manifest has an unsafe ISO filename")
  if path.name != f"{iso_name}.parts.json":
    raise ValueError("parts manifest filename does not match the ISO filename")
  for field in ("size", "part_size"):
    if type(manifest[field]) is not int or manifest[field] <= 0:
      raise ValueError(f"parts manifest has an invalid {field}")
  if manifest["part_size"] > MAX_PART_BYTES:
    raise ValueError("parts manifest exceeds the maximum release asset size")
  if not isinstance(manifest["sha256"], str) or not SHA256_PATTERN.fullmatch(manifest["sha256"]):
    raise ValueError("parts manifest has an invalid ISO checksum")
  if not isinstance(manifest["parts"], list) or not manifest["parts"]:
    raise ValueError("parts manifest has no parts")

  expected_count = (manifest["size"] + manifest["part_size"] - 1) // manifest["part_size"]
  if len(manifest["parts"]) != expected_count:
    raise ValueError("parts manifest has a missing or extra part")
  total_size = 0
  for index, part in enumerate(manifest["parts"], start=1):
    if not isinstance(part, dict) or set(part) != {"name", "size", "sha256"}:
      raise ValueError(f"parts manifest has an invalid part record at index {index}")
    expected_name = f"{iso_name}.part{index:04d}"
    if part["name"] != expected_name:
      raise ValueError(f"parts manifest has an unsafe or unordered part filename at index {index}")
    if type(part["size"]) is not int or not 1 <= part["size"] <= manifest["part_size"]:
      raise ValueError(f"parts manifest has an invalid size for {expected_name}")
    if index < expected_count and part["size"] != manifest["part_size"]:
      raise ValueError(f"non-final part has an invalid size: {expected_name}")
    if not isinstance(part["sha256"], str) or not SHA256_PATTERN.fullmatch(part["sha256"]):
      raise ValueError(f"parts manifest has an invalid checksum for {expected_name}")
    total_size += part["size"]
  if total_size != manifest["size"]:
    raise ValueError("parts manifest total does not match the ISO size")
  return cast(Manifest, manifest)


def assemble_iso(manifest_path: Path, output_dir: Path) -> Path:
  manifest = read_manifest(manifest_path)
  output_dir.mkdir(parents=True, exist_ok=True)
  destination = output_dir / manifest["iso"]
  if destination.exists() or destination.is_symlink():
    raise FileExistsError(f"refusing to overwrite existing ISO: {destination}")

  whole_digest = hashlib.sha256()
  total_size = 0
  temporary_path: Path | None = None
  try:
    with tempfile.NamedTemporaryFile(dir=output_dir, prefix=f".{destination.name}.", delete=False) as output:
      temporary_path = Path(output.name)
      for record in manifest["parts"]:
        part_path = manifest_path.parent / record["name"]
        _regular_file(part_path, "ISO part")
        part_digest = hashlib.sha256()
        part_size = 0
        with part_path.open("rb") as part:
          while block := part.read(READ_SIZE):
            output.write(block)
            part_digest.update(block)
            whole_digest.update(block)
            part_size += len(block)
            total_size += len(block)
        if part_size != record["size"] or part_digest.hexdigest() != record["sha256"]:
          raise ValueError(f"ISO part failed its size or checksum check: {record['name']}")
      output.flush()
      os.fsync(output.fileno())

    if total_size != manifest["size"] or whole_digest.hexdigest() != manifest["sha256"]:
      raise ValueError("assembled ISO failed its size or checksum check")
    os.replace(temporary_path, destination)
    temporary_path = None
    return destination
  finally:
    if temporary_path is not None:
      temporary_path.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(description=__doc__)
  subparsers = parser.add_subparsers(dest="operation", required=True)
  split_parser = subparsers.add_parser("split", help="split an ISO into release assets")
  split_parser.add_argument("iso", type=Path)
  split_parser.add_argument("--output-dir", type=Path, required=True)
  split_parser.add_argument("--part-size", type=int, default=MAX_PART_BYTES)
  assemble_parser = subparsers.add_parser("assemble", help="verify and reassemble ISO release parts")
  assemble_parser.add_argument("manifest", type=Path)
  assemble_parser.add_argument("--output-dir", type=Path, required=True)
  return parser


def main() -> int:
  arguments = _parser().parse_args()
  try:
    if arguments.operation == "split":
      result = split_iso(arguments.iso, arguments.output_dir, arguments.part_size)
    else:
      result = assemble_iso(arguments.manifest, arguments.output_dir)
  except (OSError, ValueError) as error:
    print(f"iso parts: {error}", file=sys.stderr)
    return 1
  print(result)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
