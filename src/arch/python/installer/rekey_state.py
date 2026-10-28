"""Read and atomically update the LUKS re-key journal."""

from __future__ import annotations

import os
from pathlib import Path
import re
import secrets
import stat
import sys
from typing import TypedDict

import yaml


class FilesystemSettings(TypedDict):
    file_mode: int
    directory_flags: list[str]
    read_flags: list[str]
    write_flags: list[str]
    write_mode: int
    maximum_bytes: int
    shared_sticky_mode: int
    forbidden_write_mask: int
    temporary_prefix: str
    random_bytes: int


class SyntaxSettings(TypedDict):
    key_pattern: str
    separator: str
    newline: str
    encoding: str


class StatusSettings(TypedDict):
    success: int
    missing: int
    invalid_arguments: int
    unsafe_state: int


class Settings(TypedDict):
    filesystem: FilesystemSettings
    syntax: SyntaxSettings
    statuses: StatusSettings


def _mapping(value: object, label: str) -> dict[object, object]:
    if not isinstance(value, dict):
        raise ValueError(f"invalid re-key state configuration: {label} must be a mapping")
    return {key: item for key, item in value.items()}


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"invalid re-key state configuration: {label} must be a string")
    return value


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"invalid re-key state configuration: {label} must be an integer")
    return value


def _text_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"invalid re-key state configuration: {label} must be a list of strings")
    return [item for item in value if isinstance(item, str)]


def _os_flag(name: str) -> int:
    value = getattr(os, name, None)
    if not isinstance(value, int):
        raise ValueError(f"unsupported operating system flag: {name}")
    return value


def load_settings() -> Settings:
    ap = Path(os.environ["ARCH_PATH"])
    path = ap / "data/installer/rekey-state.yml"
    with path.open(encoding="utf-8") as source:
        raw: object = yaml.safe_load(source)
    root = _mapping(raw, "root")
    settings = _mapping(root.get("rekey_state"), "rekey_state")
    filesystem = _mapping(settings.get("filesystem"), "filesystem")
    syntax = _mapping(settings.get("syntax"), "syntax")
    statuses = _mapping(settings.get("statuses"), "statuses")
    return {
        "filesystem": {
            "file_mode": _integer(filesystem.get("file_mode"), "filesystem.file_mode"),
            "directory_flags": _text_list(filesystem.get("directory_flags"), "filesystem.directory_flags"),
            "read_flags": _text_list(filesystem.get("read_flags"), "filesystem.read_flags"),
            "write_flags": _text_list(filesystem.get("write_flags"), "filesystem.write_flags"),
            "write_mode": _integer(filesystem.get("write_mode"), "filesystem.write_mode"),
            "maximum_bytes": _integer(filesystem.get("maximum_bytes"), "filesystem.maximum_bytes"),
            "shared_sticky_mode": _integer(filesystem.get("shared_sticky_mode"), "filesystem.shared_sticky_mode"),
            "forbidden_write_mask": _integer(filesystem.get("forbidden_write_mask"), "filesystem.forbidden_write_mask"),
            "temporary_prefix": _text(filesystem.get("temporary_prefix"), "filesystem.temporary_prefix"),
            "random_bytes": _integer(filesystem.get("random_bytes"), "filesystem.random_bytes"),
        },
        "syntax": {
            "key_pattern": _text(syntax.get("key_pattern"), "syntax.key_pattern"),
            "separator": _text(syntax.get("separator"), "syntax.separator"),
            "newline": _text(syntax.get("newline"), "syntax.newline"),
            "encoding": _text(syntax.get("encoding"), "syntax.encoding"),
        },
        "statuses": {
            "success": _integer(statuses.get("success"), "statuses.success"),
            "missing": _integer(statuses.get("missing"), "statuses.missing"),
            "invalid_arguments": _integer(statuses.get("invalid_arguments"), "statuses.invalid_arguments"),
            "unsafe_state": _integer(statuses.get("unsafe_state"), "statuses.unsafe_state"),
        },
    }


def directory_flags(settings: Settings) -> int:
    flags = 0
    for name in settings["filesystem"]["directory_flags"]:
        flags |= _os_flag(name)
    return flags


def open_parent(path: Path, settings: Settings, *, create: bool) -> int:
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


def read_state(directory: int, name: str, settings: Settings) -> str | None:
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


def directory_flags_read(settings: Settings) -> int:
    flags = 0
    for name in settings["filesystem"]["read_flags"]:
        flags |= _os_flag(name)
    return flags


def get_value(path: Path, key: str, settings: Settings) -> str | None:
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


def write_state(path: Path, updates: dict[str, str], settings: Settings) -> None:
    syntax = settings["syntax"]
    filesystem = settings["filesystem"]
    key_pattern = re.compile(syntax["key_pattern"])
    separator = syntax["separator"]
    newline = syntax["newline"]
    if any(not key_pattern.fullmatch(key) or separator in value or "\n" in value or "\r" in value for key, value in updates.items()):
        raise ValueError("journal update is malformed")

    directory = open_parent(path, settings, create=True)
    temporary_candidate = f"{filesystem['temporary_prefix']}{secrets.token_hex(filesystem['random_bytes'])}"
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
            temporary_candidate,
            flags,
            filesystem["write_mode"],
            dir_fd=directory,
        )
        try:
            view = memoryview(content)
            while view:
                view = view[os.write(descriptor, view):]
            os.fchmod(descriptor, filesystem["file_mode"])
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temporary_candidate, path.name, src_dir_fd=directory, dst_dir_fd=directory)
        except BaseException:
            if descriptor >= 0:
                os.close(descriptor)
                descriptor = -1
            try:
                os.unlink(temporary_candidate, dir_fd=directory)
            except FileNotFoundError:
                pass
            raise
        os.fsync(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(directory)


def main(arguments: list[str] | None = None) -> int:
    args = sys.argv[1:] if arguments is None else arguments
    try:
        settings = load_settings()
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        print(f"Could not load re-key state settings: {error}", file=sys.stderr)
        return 1
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
