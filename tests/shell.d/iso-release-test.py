"""Check ISO release part splitting, verification, and atomic assembly."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile

from base_test import ROOT, fail_check, pass_check


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
