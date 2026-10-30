"""Split an ISO and upload its parts to an existing GitHub release."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .config import load_config
from .parts import read_manifest, split_iso


def upload_release(iso: Path, repository: str, tag: str) -> None:
    release = load_config()["release"]
    messages = release["messages"]
    if not re.fullmatch(release["repository_pattern"], repository):
        raise ValueError(messages["repository_invalid"])
    if not re.fullmatch(release["tag_pattern"], tag):
        raise ValueError(messages["tag_invalid"])
    github = release["github_command"]
    if shutil.which(github) is None:
        raise RuntimeError(messages["upload_github_cli_required"])

    with tempfile.TemporaryDirectory(
        prefix=release["upload_directory_prefix"]
    ) as temporary:
        assets_dir = Path(temporary)
        manifest = split_iso(iso, assets_dir)
        parts_manifest = read_manifest(manifest)
        parts = [assets_dir / record["name"] for record in parts_manifest["parts"]]
        subprocess.run(
            [
                github,
                *release["upload_command"],
                tag,
                release["upload_repository_option"],
                repository,
                str(manifest),
                *(str(part) for part in parts),
            ],
            check=True,
            timeout=int(release["upload_timeout_seconds"]),
        )


def main(argv: list[str] | None = None) -> int:
    release = load_config()["release"]
    upload = release["upload"]
    messages = release["messages"]
    parser = argparse.ArgumentParser(description=upload["parser_description"])
    parser.add_argument(upload["iso_argument"], type=Path)
    parser.add_argument(upload["tag_argument"], help=upload["tag_help"])
    parser.add_argument(
        upload["repository_option"],
        default=release["default_repository"],
        help=upload["repository_help"],
    )
    arguments = parser.parse_args(argv)
    try:
        upload_release(arguments.iso, arguments.repo, arguments.tag)
    except subprocess.TimeoutExpired:
        print(
            messages["upload_timeout"].format(
                seconds=release["upload_timeout_seconds"]
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
