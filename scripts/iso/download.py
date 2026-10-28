"""Download and verify the ISO parts attached to a GitHub release."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.iso.parts import assemble_iso, read_manifest


REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
TAG_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\Z")


def download_release(repository: str, tag: str, output_dir: Path) -> Path:
  if not REPOSITORY_PATTERN.fullmatch(repository):
    raise ValueError("repository must use owner/repository format")
  if not TAG_PATTERN.fullmatch(tag):
    raise ValueError("release tag contains unsupported characters")
  if shutil.which("gh") is None:
    raise RuntimeError("GitHub CLI (gh) is required to download release assets")

  output_dir.mkdir(parents=True, exist_ok=True)
  with tempfile.TemporaryDirectory(prefix="arch-iso-release-") as temporary:
    download_dir = Path(temporary)
    command = ["gh", "release", "download", tag, "--repo", repository, "--dir", str(download_dir)]
    subprocess.run([*command, "--pattern", "*.iso.parts.json"], check=True)
    manifests = list(download_dir.glob("*.iso.parts.json"))
    if len(manifests) != 1:
      raise ValueError("release must contain exactly one ISO parts manifest")
    manifest_path = manifests[0]
    manifest = read_manifest(manifest_path)
    for record in manifest["parts"]:
      subprocess.run([*command, "--pattern", record["name"]], check=True)
    return assemble_iso(manifest_path, output_dir)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("tag", help="GitHub release tag")
  parser.add_argument("--repo", default="kairosci/os", help="GitHub repository (owner/repository)")
  parser.add_argument("--output-dir", type=Path, default=Path.cwd())
  arguments = parser.parse_args()
  try:
    result = download_release(arguments.repo, arguments.tag, arguments.output_dir)
  except (OSError, RuntimeError, subprocess.CalledProcessError, ValueError) as error:
    print(f"iso download: {error}", file=sys.stderr)
    return 1
  print(result)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
