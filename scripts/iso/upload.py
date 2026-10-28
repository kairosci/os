"""Split an ISO and upload its parts to an existing GitHub release."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.iso.parts import split_iso


REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
TAG_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\Z")


def upload_release(iso: Path, repository: str, tag: str) -> None:
  if not REPOSITORY_PATTERN.fullmatch(repository):
    raise ValueError("repository must use owner/repository format")
  if not TAG_PATTERN.fullmatch(tag):
    raise ValueError("release tag contains unsupported characters")
  if shutil.which("gh") is None:
    raise RuntimeError("GitHub CLI (gh) is required to upload release assets")

  with tempfile.TemporaryDirectory(prefix="arch-iso-release-") as temporary:
    assets_dir = Path(temporary)
    manifest = split_iso(iso, assets_dir)
    parts = sorted(assets_dir.glob(f"{iso.name}.part*"))
    subprocess.run(
      ["gh", "release", "upload", tag, "--repo", repository, "--verify-tag", str(manifest), *(str(part) for part in parts)],
      check=True,
    )


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("iso", type=Path)
  parser.add_argument("tag", help="existing GitHub release tag")
  parser.add_argument("--repo", default="kairosci/os", help="GitHub repository (owner/repository)")
  arguments = parser.parse_args()
  try:
    upload_release(arguments.iso, arguments.repo, arguments.tag)
  except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as error:
    print(f"iso upload: {error}", file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
