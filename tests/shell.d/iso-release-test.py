"""Check ISO release part splitting, verification, and atomic assembly."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from base_test import ROOT, fail_check, pass_check, test_environment


sys.path.insert(0, str(ROOT))
os.environ["AP"] = str(ROOT)
from scripts.iso.config import load_config
from scripts.iso.parts import assemble_iso, read_manifest, split_iso

max_part_bytes = load_config()["release"]["max_part_bytes"]


with tempfile.TemporaryDirectory(prefix="arch-iso-parts-test-") as temporary:
  stage = Path(temporary)
  source = stage / "arch-4.0.6.iso"
  payload = bytes(range(23))
  source.write_bytes(payload)
  assets = stage / "release-assets"
  manifest_path = split_iso(source, assets, part_size=7)
  manifest = read_manifest(manifest_path)
  assert [part["size"] for part in manifest["parts"]] == [7, 7, 7, 2]
  assert all(part["size"] < 2_000_000_000 for part in manifest["parts"])
  assembled = assemble_iso(manifest_path, stage / "assembled")
  assert assembled.read_bytes() == payload
  pass_check("split ISO parts are bounded, checksummed, and reassemble byte-for-byte")

  cli_assets = stage / "cli-release-assets"
  cli_result = subprocess.run(
    [
      str(ROOT / "src/arch/commands/archctl"),
      "iso",
      "parts",
      "split",
      str(source),
      "--output-dir",
      str(cli_assets),
      "--part-size",
      "7",
    ],
    check=False,
    capture_output=True,
    text=True,
    env=test_environment(),
  )
  assert cli_result.returncode == 0, cli_result.stderr
  assert read_manifest(Path(cli_result.stdout.strip()))["iso"] == source.name
  pass_check("archctl ISO parts route invokes the configured splitter")

  github_assets = stage / "github-assets"
  github_assets.mkdir()
  github_manifest = split_iso(source, github_assets, part_size=7)
  metadata = github_assets / "metadata.json"
  metadata.write_text(
    json.dumps(
      {
        "assets": [
          {"name": path.name, "size": path.stat().st_size}
          for path in sorted(github_assets.iterdir())
          if path.name != metadata.name
        ]
      }
    ),
    encoding="utf-8",
  )
  fake_bin = stage / "fake-bin"
  fake_bin.mkdir()
  fake_gh = fake_bin / "gh"
  fake_gh.write_text(
    "#!/usr/bin/python3\n"
    "import json, os, shutil, sys\n"
    "from pathlib import Path\n"
    "args = sys.argv[1:]\n"
    "assets = Path(os.environ['ISO_TEST_ASSET_DIR'])\n"
    "if args[:2] == ['release', 'view']:\n"
    "  print(Path(os.environ['ISO_TEST_ASSET_METADATA']).read_text())\n"
    "elif args[:2] == ['release', 'download']:\n"
    "  destination = Path(args[args.index('--dir') + 1])\n"
    "  patterns = [args[index + 1] for index, value in enumerate(args[:-1]) if value == '--pattern']\n"
    "  for pattern in patterns:\n"
    "    for asset in assets.glob(pattern):\n"
    "      shutil.copyfile(asset, destination / asset.name)\n"
    "else:\n"
    "  raise SystemExit(2)\n",
    encoding="utf-8",
  )
  fake_gh.chmod(0o755)
  download_dir = stage / "downloaded"
  download_result = subprocess.run(
    [
      str(ROOT / "src/arch/commands/archctl"),
      "iso",
      "download",
      "v-test",
      "--repo",
      "owner/repository",
      "--output-dir",
      str(download_dir),
      "--iso",
      source.name,
    ],
    check=False,
    capture_output=True,
    text=True,
    env=test_environment(
      PATH=f"{fake_bin}:{os.environ.get('PATH', '')}",
      ISO_TEST_ASSET_DIR=str(github_assets),
      ISO_TEST_ASSET_METADATA=str(metadata),
    ),
  )
  assert download_result.returncode == 0, download_result.stderr
  downloaded_iso = Path(download_result.stdout.strip())
  assert downloaded_iso.read_bytes() == payload
  assert github_manifest.is_file()
  pass_check("archctl ISO download verifies release assets and assembles the complete image")

  broken_manifest = stage / "broken.parts.json"
  broken = dict(manifest)
  broken["part_size"] = max_part_bytes + 1
  broken_manifest.write_text(json.dumps(broken), encoding="utf-8")
  try:
    read_manifest(broken_manifest)
  except ValueError:
    pass
  else:
    fail_check("oversized release part limits are rejected")
  pass_check("manifest cannot declare a part above the release asset limit")

  try:
    split_iso(source, stage / "oversized-split", part_size=max_part_bytes + 1)
  except ValueError:
    pass
  else:
    fail_check("splitter rejects a configured part size above the release asset limit")
  pass_check("splitter cannot create an oversized release asset")

  missing_assets = stage / "missing"
  missing_assets.mkdir()
  missing_manifest = missing_assets / manifest_path.name
  missing_manifest.write_bytes(manifest_path.read_bytes())
  try:
    assemble_iso(missing_manifest, stage / "missing-output")
  except ValueError as error:
    assert "does not exist" in str(error)
  else:
    fail_check("missing release parts are rejected")
  assert not (stage / "missing-output" / source.name).exists()
  pass_check("missing parts do not publish a partial ISO")

  first_part = assets / manifest["parts"][0]["name"]
  first_part.write_bytes(b"corrupt")
  try:
    assemble_iso(manifest_path, stage / "corrupt-output")
  except ValueError as error:
    assert "failed its size or checksum" in str(error)
  else:
    fail_check("corrupt release parts are rejected")
  assert not (stage / "corrupt-output" / source.name).exists()
  pass_check("corrupt parts do not publish an ISO")
