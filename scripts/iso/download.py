"""Download and verify the ISO parts attached to a GitHub release."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .config import ReleaseSettings, load_config
from .parts import assemble_iso, read_manifest


def _release_assets(
    github: str, release: ReleaseSettings, tag: str, repository: str
) -> dict[str, int]:
    messages = release["messages"]
    command = [
        github,
        *(
            argument.format(tag=tag, repository=repository)
            for argument in release["release_metadata_command"]
        ),
    ]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=int(release["release_metadata_timeout_seconds"]),
    )
    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(messages["release_metadata_invalid"]) from error
    asset_field = release["asset_list_field"]
    name_field = release["asset_name_field"]
    size_field = release["asset_size_field"]
    if not isinstance(metadata, dict) or not isinstance(metadata.get(asset_field), list):
        raise TypeError(messages["release_metadata_invalid"])
    records = metadata[asset_field]
    if len(records) > int(release["maximum_release_asset_count"]):
        raise ValueError(messages["release_asset_count_limit"])

    asset_limit = int(release["github_asset_limit_bytes"])
    manifest_limit = int(release["manifest_max_bytes"])
    manifest_suffix = release["manifest_suffix"]
    assets: dict[str, int] = {}
    for record in records:
        if not isinstance(record, dict):
            raise TypeError(messages["release_metadata_invalid"])
        name = record.get(name_field)
        size = record.get(size_field)
        if (
            not isinstance(name, str)
            or name in {".", ".."}
            or "/" in name
            or "\\" in name
            or type(size) is not int
            or size < 0
        ):
            raise ValueError(messages["release_metadata_invalid"])
        if name in assets:
            raise ValueError(messages["release_asset_duplicate"].format(name=name))
        if size >= asset_limit:
            raise ValueError(messages["release_asset_too_large"].format(name=name))
        if name.endswith(manifest_suffix) and size > manifest_limit:
            raise ValueError(messages["release_manifest_too_large"].format(name=name))
        assets[name] = size
    return assets


def download_release(
    repository: str, tag: str, output_dir: Path, iso_name: str | None = None
) -> Path:
    release = load_config()["release"]
    messages = release["messages"]
    if not re.fullmatch(release["repository_pattern"], repository):
        raise ValueError(messages["repository_invalid"])
    if not re.fullmatch(release["tag_pattern"], tag):
        raise ValueError(messages["tag_invalid"])
    github = release["github_command"]
    if shutil.which(github) is None:
        raise RuntimeError(messages["github_cli_required"])

    release_assets = _release_assets(github, release, tag, repository)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=release["download_directory_prefix"]
    ) as temporary:
        download_dir = Path(temporary)
        command = [
            github,
            *(
                argument.format(
                    tag=tag,
                    repository=repository,
                    directory=download_dir,
                )
                for argument in release["download_command"]
            ),
        ]
        manifest_pattern = f"*{release['manifest_suffix']}"
        pattern_arguments = [
            argument.format(pattern=manifest_pattern)
            for argument in release["download_pattern_arguments"]
        ]
        subprocess.run(
            [*command, *pattern_arguments],
            check=True,
            timeout=int(release["download_timeout_seconds"]),
        )
        manifests = sorted(download_dir.glob(manifest_pattern))
        if not manifests:
            raise ValueError(messages["missing_manifest"])
        if iso_name is not None:
            manifests = [
                path for path in manifests if read_manifest(path)["iso"] == iso_name
            ]
            if not manifests:
                available = ", ".join(
                    read_manifest(path)["iso"]
                    for path in sorted(download_dir.glob(manifest_pattern))
                )
                raise ValueError(
                    messages["selected_iso_missing"].format(
                        iso=iso_name, available=available
                    )
                )
        if len(manifests) != 1:
            available = ", ".join(read_manifest(path)["iso"] for path in manifests)
            raise ValueError(messages["multiple_isos"].format(available=available))
        manifest_path = manifests[0]
        manifest_size = release_assets.get(manifest_path.name)
        if manifest_size is None:
            raise ValueError(
                messages["release_asset_missing"].format(name=manifest_path.name)
            )
        if manifest_path.stat().st_size != manifest_size:
            raise ValueError(
                messages["release_asset_size_mismatch"].format(
                    name=manifest_path.name
                )
            )
        manifest = read_manifest(manifest_path)
        part_patterns: list[str] = []
        for record in manifest["parts"]:
            asset_size = release_assets.get(record["name"])
            if asset_size is None:
                raise ValueError(
                    messages["release_asset_missing"].format(name=record["name"])
                )
            if asset_size != record["size"]:
                raise ValueError(
                    messages["release_asset_size_mismatch"].format(
                        name=record["name"]
                    )
                )
            part_patterns.extend(
                argument.format(pattern=record["name"])
                for argument in release["download_pattern_arguments"]
            )
        subprocess.run(
            [*command, *part_patterns],
            check=True,
            timeout=int(release["download_timeout_seconds"]),
        )
        return assemble_iso(manifest_path, output_dir)


def main(argv: list[str] | None = None) -> int:
    release = load_config()["release"]
    download = release["download"]
    messages = release["messages"]
    parser = argparse.ArgumentParser(description=download["parser_description"])
    parser.add_argument(download["tag_argument"], help=download["tag_help"])
    parser.add_argument(
        download["repository_option"],
        default=release["default_repository"],
        help=download["repository_help"],
    )
    parser.add_argument(
        download["output_directory_option"],
        type=Path,
        default=Path.cwd(),
        help=download["output_directory_help"],
    )
    parser.add_argument(
        download["iso_option"],
        help=messages["iso_selection_help"],
    )
    arguments = parser.parse_args(argv)
    try:
        result = download_release(
            arguments.repo, arguments.tag, arguments.output_dir, arguments.iso
        )
    except (
        OSError,
        RuntimeError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        TypeError,
        ValueError,
    ) as error:
        print(f"{messages['download_error_prefix']}{error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
