"""Read and atomically update the LUKS re-key journal."""

from __future__ import annotations

import os
from pathlib import Path
import re
import secrets
import stat
import sys
from typing import Any

import yaml


def load_settings() -> dict[str, Any]:
    ap = Path(os.environ["ARCH_PATH"])
    path = ap / "data/installer/rekey-state.yml"
    with path.open(encoding="utf-8") as source:
        return yaml.safe_load(source)["rekey_state"]


def directory_flags(settings: dict[str, Any]) -> int:
    flags = 0
    for name in settings["filesystem"]["directory_flags"]:
        flags |= getattr(os, name)
    return flags


def open_parent(path: Path, settings: dict[str, Any], *, create: bool) -> int:
    filesystem = settings["filesystem"]
    if not path.is_absolute() or not path.name or any(part in (".", "..") for part in path.parts):
        raise ValueError("journal path is not a normalized absolute path")

    descriptor = os.open("/", directory_flags(settings))
    try:
        for component in path.parts[1:-1]:
            try:
                child = os.open(component, directory_flags(settings), dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(component, 0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
                child = os.open(component, directory_flags(settings), dir_fd=descriptor)

            metadata = os.fstat(child)
            writable = metadata.st_mode & filesystem["forbidden_write_mask"]
            shared_sticky = (
                metadata.st_uid == 0
                and metadata.st_mode & filesystem["shared_sticky_mode"]
                and metadata.st_mode & stat.S_IWOTH
            )
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid not in (0, os.geteuid())
                or (writable and not shared_sticky)
            ):
                os.close(child)
                raise PermissionError("journal parent directory is not trusted")
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def read_state(directory: int, name: str, settings: dict[str, Any]) -> str | None:
    filesystem = settings["filesystem"]
    try:
        descriptor = os.open(name, directory_flags_read(settings), dir_fd=directory)
    except FileNotFoundError:
        return None
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.geteuid()
            or metadata.st_mode & filesystem["forbidden_write_mask"]
            or metadata.st_size > filesystem["maximum_bytes"]
        ):
            raise PermissionError("journal file is not trusted")
        with os.fdopen(descriptor, "rb") as source:
            descriptor = -1
            content = source.read(filesystem["maximum_bytes"] + 1)
        if len(content) > filesystem["maximum_bytes"]:
            raise ValueError("journal file exceeds its configured size limit")
        return content.decode(settings["syntax"]["encoding"])
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def directory_flags_read(settings: dict[str, Any]) -> int:
    flags = 0
    for name in settings["filesystem"]["read_flags"]:
        flags |= getattr(os, name)
    return flags


def get_value(path: Path, key: str, settings: dict[str, Any]) -> str | None:
    directory = open_parent(path, settings, create=False)
    try:
        content = read_state(directory, path.name, settings)
    finally:
        os.close(directory)
    if content is None:
        return None
    separator = settings["syntax"]["separator"]
    for line in content.splitlines():
        current, found, value = line.partition(separator)
        if found and current == key:
            return value
    return None


def write_state(path: Path, updates: dict[str, str], settings: dict[str, Any]) -> None:
    syntax = settings["syntax"]
    filesystem = settings["filesystem"]
    key_pattern = re.compile(syntax["key_pattern"])
    separator = syntax["separator"]
    newline = syntax["newline"]
    if any(not key_pattern.fullmatch(key) or separator in value or "\n" in value or "\r" in value for key, value in updates.items()):
        raise ValueError("journal update is malformed")

    directory = open_parent(path, settings, create=True)
    temporary_name = f"{filesystem['temporary_prefix']}{secrets.token_hex(filesystem['random_bytes'])}"
    temporary_created = False
    descriptor = -1
    try:
        previous = read_state(directory, path.name, settings)
        lines = []
        if previous is not None:
            lines = [
                line for line in previous.splitlines()
                if line and line.partition(separator)[0] not in updates
            ]
        lines.extend(f"{key}{separator}{value}" for key, value in updates.items())
        content = (newline.join(lines) + newline).encode(syntax["encoding"])

        flags = 0
        for name in filesystem["write_flags"]:
            flags |= getattr(os, name)
        descriptor = os.open(
            temporary_name,
            flags,
            filesystem["write_mode"],
            dir_fd=directory,
        )
        temporary_created = True
        view = memoryview(content)
        while view:
            view = view[os.write(descriptor, view):]
        os.fchmod(descriptor, filesystem["file_mode"])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary_name, path.name, src_dir_fd=directory, dst_dir_fd=directory)
        temporary_created = False
        os.fsync(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_created:
            try:
                os.unlink(temporary_name, dir_fd=directory)
            except FileNotFoundError:
                pass
        os.close(directory)


def main(arguments: list[str] | None = None) -> int:
    args = sys.argv[1:] if arguments is None else arguments
    settings = load_settings()
    statuses = settings["statuses"]
    if len(args) < 3 or args[0] not in ("get", "put"):
        return statuses["invalid_arguments"]

    path = Path(args[1])
    try:
        if args[0] == "get" and len(args) == 3:
            value = get_value(path, args[2], settings)
            if value is None:
                return statuses["missing"]
            sys.stdout.write(value + settings["syntax"]["newline"])
            return statuses["success"]
        if args[0] == "put" and len(args) >= 4 and len(args[2:]) % 2 == 0:
            write_state(path, dict(zip(args[2::2], args[3::2], strict=True)), settings)
            return statuses["success"]
    except FileNotFoundError:
        return statuses["missing"]
    except (OSError, ValueError, UnicodeError, yaml.YAMLError):
        return statuses["unsafe_state"]
    return statuses["invalid_arguments"]


if __name__ == "__main__":
    raise SystemExit(main())
