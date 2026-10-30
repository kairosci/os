"""Publish verified ArchISO release assets from CI build artifacts."""

from __future__ import annotations

import argparse
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from .config import load_config
from .parts import read_manifest


def release_asset_paths(directory: Path) -> list[Path]:
    settings = load_config()["release"]
    messages = settings["messages"]
    asset_limit = int(settings["github_asset_limit_bytes"])
    manifest_suffix = settings["manifest_suffix"]
    iso_pattern = re.compile(settings["iso_name_pattern"])
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(
            messages["upload_assets_directory_invalid"].format(path=directory)
        )

    manifests = sorted(directory.glob(f"*{manifest_suffix}"))
    expected_names: set[str] = set()
    upload_paths: list[Path] = []
    image_count = 0
    for manifest_path in manifests:
        manifest = read_manifest(manifest_path)
        image_name = manifest["iso"]
        if not iso_pattern.fullmatch(image_name) or ".." in image_name:
            raise ValueError(messages["parts_manifest_iso_name"])
        expected_names.add(manifest_path.name)
        image_count += 1
        for record in manifest["parts"]:
            part_path = directory / record["name"]
            metadata = part_path.lstat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != record["size"]:
                raise ValueError(
                    messages["parts_manifest_part_size"].format(name=record["name"])
                )
            expected_names.add(part_path.name)
            if metadata.st_size >= asset_limit:
                raise ValueError(
                    messages["release_asset_too_large"].format(name=part_path.name)
                )
            upload_paths.append(part_path)

        image_path = directory / image_name
        metadata = image_path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != manifest["size"]:
            raise ValueError(
                messages["release_image_size_mismatch"].format(name=image_name)
            )
        expected_names.add(image_path.name)
        if metadata.st_size < asset_limit:
            upload_paths.append(image_path)
        else:
            print(
                messages["upload_skipping_oversized_iso"].format(name=image_name),
                file=sys.stderr,
            )
        upload_paths.append(manifest_path)

    if image_count == 0:
        raise ValueError(messages["missing_manifest"])
    actual_names: set[str] = set()
    for path in directory.iterdir():
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(messages["upload_asset_not_regular"].format(path=path))
        actual_names.add(path.name)
    if actual_names != expected_names:
        raise ValueError(messages["upload_assets_mismatch"])
    if len(upload_paths) > int(settings["maximum_release_asset_count"]):
        raise ValueError(messages["release_asset_count_limit"])
    return sorted(upload_paths)


def publish_release_assets(directory: Path, repository: str, tag: str) -> None:
    settings = load_config()["release"]
    messages = settings["messages"]
    if not re.fullmatch(settings["repository_pattern"], repository):
        raise ValueError(messages["repository_invalid"])
    if not re.fullmatch(settings["tag_pattern"], tag):
        raise ValueError(messages["tag_invalid"])
    github = settings["github_command"]
    if shutil.which(github) is None:
        raise RuntimeError(messages["upload_github_cli_required"])
    assets = release_asset_paths(directory)
    subprocess.run(
        [
            github,
            *settings["upload_command"],
            tag,
            settings["upload_repository_option"],
            repository,
            settings["upload_clobber_option"],
            *(str(path) for path in assets),
        ],
        check=True,
        timeout=int(settings["upload_timeout_seconds"]),
    )


def main(argv: list[str] | None = None) -> int:
    settings = load_config()["release"]
    upload = settings["upload"]
    messages = settings["messages"]
    parser = argparse.ArgumentParser(
        description=upload["release_assets_parser_description"]
    )
    parser.add_argument(upload["tag_argument"], help=upload["tag_help"])
    parser.add_argument(
        upload["repository_option"],
        default=settings["default_repository"],
        help=upload["repository_help"],
    )
    parser.add_argument(upload["release_assets_directory_option"], type=Path)
    arguments = parser.parse_args(argv)
    try:
        publish_release_assets(arguments.assets_dir, arguments.repo, arguments.tag)
    except subprocess.TimeoutExpired:
        print(
            messages["upload_timeout"].format(
                seconds=settings["upload_timeout_seconds"]
            ),
            file=sys.stderr,
        )
        return 1
    except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as error:
        print(f"{messages['upload_error_prefix']}{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
