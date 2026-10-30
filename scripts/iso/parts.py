"""Split and reassemble ISO release assets within GitHub's asset size limit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import BinaryIO, TypedDict, cast

from .config import ReleaseSettings, load_config


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


def _regular_file(
    path: Path, description: str, messages: dict[str, str]
) -> os.stat_result:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise ValueError(
            messages["parts_iso_missing"].format(description=description, path=path)
        ) from error
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError(
            messages["parts_regular_file"].format(description=description, path=path)
        )
    return metadata


def _open_regular_file(
    path: Path, description: str, messages: dict[str, str]
) -> BinaryIO:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
        )
    except OSError:
        _regular_file(path, description, messages)
        raise
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(
                messages["parts_regular_file"].format(
                    description=description, path=path
                )
            )
        return os.fdopen(descriptor, "rb")
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def _configured_part_limit(
    release: ReleaseSettings, messages: dict[str, str]
) -> int:
    asset_limit = int(release["github_asset_limit_bytes"])
    part_limit = int(release["max_part_bytes"])
    if not 0 < part_limit < asset_limit:
        raise ValueError(messages["parts_config_limit_invalid"])
    return part_limit


def _write_json(path: Path, value: Manifest) -> None:
    release = load_config()["release"]
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f"{release['split_temporary_prefix']}{path.name}.",
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
        try:
            json.dump(value, temporary, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            os.link(temporary_path, path)
            temporary_path.unlink()
        finally:
            temporary_path.unlink(missing_ok=True)


def split_iso(source: Path, output_dir: Path, part_size: int | None = None) -> Path:
    release = load_config()["release"]
    messages = release["messages"]
    parts_config = release["parts"]
    maximum_part_bytes = _configured_part_limit(release, messages)
    read_size = int(release["read_size_bytes"])
    if part_size is None:
        part_size = maximum_part_bytes
    iso_name_pattern = re.compile(release["iso_name_pattern"])
    metadata = _regular_file(source, parts_config["iso_label"], messages)
    if not iso_name_pattern.fullmatch(source.name) or ".." in source.name:
        raise ValueError(messages["parts_iso_name_invalid"])
    if not 1 <= part_size <= maximum_part_bytes:
        raise ValueError(
            messages["parts_size_out_of_range"].format(maximum=maximum_part_bytes)
        )
    if metadata.st_size <= 0:
        raise ValueError(messages["parts_iso_empty"])

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"{source.name}{release['manifest_suffix']}"
    part_count = (metadata.st_size + part_size - 1) // part_size
    maximum_part_count = int(release["maximum_part_count"])
    if part_count > maximum_part_count:
        raise ValueError(
            messages["parts_count_limit"].format(maximum=maximum_part_count)
        )
    part_paths = [
        output_dir / release["part_name_format"].format(iso=source.name, index=index)
        for index in range(1, part_count + 1)
    ]
    conflicts = [
        path.name
        for path in [manifest_path, *part_paths]
        if path.exists() or path.is_symlink()
    ]
    if conflicts:
        raise FileExistsError(
            messages["parts_existing_assets"].format(names=", ".join(conflicts))
        )

    whole_digest = hashlib.new(release["checksum_algorithm"])
    parts: list[PartRecord] = []
    created: list[Path] = []
    processed = 0
    try:
        with _open_regular_file(
            source, parts_config["iso_label"], messages
        ) as input_stream:
            for part_path in part_paths:
                remaining = min(part_size, metadata.st_size - processed)
                part_digest = hashlib.new(release["checksum_algorithm"])
                written = 0
                with tempfile.NamedTemporaryFile(
                    dir=output_dir,
                    prefix=f"{release['split_temporary_prefix']}{part_path.name}.",
                    delete=False,
                ) as temporary:
                    temporary_path = Path(temporary.name)
                    created.append(temporary_path)
                    while remaining:
                        block = input_stream.read(min(read_size, remaining))
                        if not block:
                            raise ValueError(messages["parts_iso_truncated"])
                        temporary.write(block)
                        part_digest.update(block)
                        whole_digest.update(block)
                        written += len(block)
                        remaining -= len(block)
                        processed += len(block)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                os.link(temporary_path, part_path)
                created.append(part_path)
                temporary_path.unlink()
                created.remove(temporary_path)
                parts.append(
                    {
                        "name": part_path.name,
                        "size": written,
                        "sha256": part_digest.hexdigest(),
                    }
                )

            if input_stream.read(1):
                raise ValueError(messages["parts_iso_grew"])

        manifest: Manifest = {
            "format": int(release["manifest_format"]),
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
    release = load_config()["release"]
    messages = release["messages"]
    parts_config = release["parts"]
    max_part_bytes = _configured_part_limit(release, messages)
    manifest_format = int(release["manifest_format"])
    sha256_pattern = re.compile(release["sha256_pattern"])
    iso_name_pattern = re.compile(release["iso_name_pattern"])
    manifest_max_bytes = int(release["manifest_max_bytes"])
    with _open_regular_file(path, parts_config["manifest_label"], messages) as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(
                messages["parts_regular_file"].format(
                    description=parts_config["manifest_label"], path=path
                )
            )
        if metadata.st_size > manifest_max_bytes:
            raise ValueError(
                messages["parts_manifest_too_large"].format(
                    maximum=manifest_max_bytes
                )
            )
        manifest_data = stream.read(manifest_max_bytes + 1)
        if len(manifest_data) > manifest_max_bytes:
            raise ValueError(
                messages["parts_manifest_too_large"].format(
                    maximum=manifest_max_bytes
                )
            )
        try:
            manifest = json.loads(manifest_data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(
                messages["parts_manifest_invalid"].format(path=path)
            ) from error
    if not isinstance(manifest, dict) or set(manifest) != {
        "format",
        "iso",
        "size",
        "sha256",
        "part_size",
        "parts",
    }:
        raise ValueError(messages["parts_manifest_schema"])
    if type(manifest["format"]) is not int or manifest["format"] != int(
        manifest_format
    ):
        raise ValueError(messages["parts_manifest_version"])
    iso_name = manifest["iso"]
    if (
        not isinstance(iso_name, str)
        or not iso_name_pattern.fullmatch(iso_name)
        or ".." in iso_name
    ):
        raise ValueError(messages["parts_manifest_iso_name"])
    if path.name != f"{iso_name}{release['manifest_suffix']}":
        raise ValueError(messages["parts_manifest_iso_mismatch"])
    for field in ("size", "part_size"):
        if type(manifest[field]) is not int or manifest[field] <= 0:
            raise ValueError(
                messages["parts_manifest_field_invalid"].format(field=field)
            )
    if manifest["part_size"] > max_part_bytes:
        raise ValueError(messages["parts_manifest_part_limit"])
    if not isinstance(manifest["sha256"], str) or not sha256_pattern.fullmatch(
        manifest["sha256"]
    ):
        raise ValueError(messages["parts_manifest_checksum"])
    if not isinstance(manifest["parts"], list) or not manifest["parts"]:
        raise ValueError(messages["parts_manifest_no_parts"])

    expected_count = (manifest["size"] + manifest["part_size"] - 1) // manifest[
        "part_size"
    ]
    maximum_part_count = int(release["maximum_part_count"])
    if expected_count > maximum_part_count:
        raise ValueError(
            messages["parts_count_limit"].format(maximum=maximum_part_count)
        )
    if len(manifest["parts"]) != expected_count:
        raise ValueError(messages["parts_manifest_count"])
    total_size = 0
    for index, part in enumerate(manifest["parts"], start=1):
        if not isinstance(part, dict) or set(part) != {"name", "size", "sha256"}:
            raise ValueError(messages["parts_manifest_record"].format(index=index))
        expected_name = release["part_name_format"].format(iso=iso_name, index=index)
        if part["name"] != expected_name:
            raise ValueError(messages["parts_manifest_part_name"].format(index=index))
        if (
            type(part["size"]) is not int
            or not 1 <= part["size"] <= manifest["part_size"]
        ):
            raise ValueError(
                messages["parts_manifest_part_size"].format(name=expected_name)
            )
        if index < expected_count and part["size"] != manifest["part_size"]:
            raise ValueError(
                messages["parts_manifest_nonfinal_size"].format(name=expected_name)
            )
        if not isinstance(part["sha256"], str) or not sha256_pattern.fullmatch(
            part["sha256"]
        ):
            raise ValueError(
                messages["parts_manifest_part_checksum"].format(name=expected_name)
            )
        total_size += part["size"]
    if total_size != manifest["size"]:
        raise ValueError(messages["parts_manifest_total"])
    return cast(Manifest, manifest)


def assemble_iso(manifest_path: Path, output_dir: Path) -> Path:
    release = load_config()["release"]
    messages = release["messages"]
    parts_config = release["parts"]
    read_size = int(release["read_size_bytes"])
    manifest = read_manifest(manifest_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / manifest["iso"]
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(messages["parts_existing_iso"].format(path=destination))

    whole_digest = hashlib.new(release["checksum_algorithm"])
    total_size = 0
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output_dir,
            prefix=f"{release['split_temporary_prefix']}{destination.name}.",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            for record in manifest["parts"]:
                part_path = manifest_path.parent / record["name"]
                part_digest = hashlib.new(release["checksum_algorithm"])
                part_size = 0
                with _open_regular_file(
                    part_path, parts_config["part_label"], messages
                ) as part:
                    while block := part.read(read_size):
                        output.write(block)
                        part_digest.update(block)
                        whole_digest.update(block)
                        part_size += len(block)
                        total_size += len(block)
                if (
                    part_size != record["size"]
                    or part_digest.hexdigest() != record["sha256"]
                ):
                    raise ValueError(
                        messages["parts_part_checksum_failed"].format(
                            name=record["name"]
                        )
                    )
            output.flush()
            os.fsync(output.fileno())

        if (
            total_size != manifest["size"]
            or whole_digest.hexdigest() != manifest["sha256"]
        ):
            raise ValueError(messages["parts_assembly_checksum_failed"])
        os.link(temporary_path, destination)
        temporary_path.unlink()
        temporary_path = None
        return destination
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _parser(
    parts_config: dict[str, str], messages: dict[str, str], maximum_part_bytes: int
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=parts_config["parser_description"])
    subparsers = parser.add_subparsers(
        dest=parts_config["operation_destination"], required=True
    )
    split_parser = subparsers.add_parser(
        parts_config["split_operation"], help=messages["parts_split_help"]
    )
    split_parser.add_argument(parts_config["iso_argument"], type=Path)
    split_parser.add_argument(
        parts_config["output_directory_option"],
        dest=parts_config["output_directory_destination"],
        type=Path,
        required=True,
    )
    split_parser.add_argument(
        parts_config["part_size_option"],
        dest=parts_config["part_size_destination"],
        type=int,
        default=maximum_part_bytes,
    )
    assemble_parser = subparsers.add_parser(
        parts_config["assemble_operation"], help=messages["parts_assemble_help"]
    )
    assemble_parser.add_argument(parts_config["manifest_argument"], type=Path)
    assemble_parser.add_argument(
        parts_config["output_directory_option"],
        dest=parts_config["output_directory_destination"],
        type=Path,
        required=True,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    release = load_config()["release"]
    parts_config = release["parts"]
    messages = release["messages"]
    try:
        maximum_part_bytes = _configured_part_limit(release, messages)
        arguments = _parser(parts_config, messages, maximum_part_bytes).parse_args(
            argv
        )
        if (
            getattr(arguments, parts_config["operation_destination"])
            == parts_config["split_operation"]
        ):
            result = split_iso(
                getattr(arguments, parts_config["iso_argument"]),
                getattr(arguments, parts_config["output_directory_destination"]),
                getattr(arguments, parts_config["part_size_destination"]),
            )
        else:
            result = assemble_iso(
                getattr(arguments, parts_config["manifest_argument"]),
                getattr(arguments, parts_config["output_directory_destination"]),
            )
    except (OSError, ValueError) as error:
        print(f"{messages['parts_error_prefix']}{error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
