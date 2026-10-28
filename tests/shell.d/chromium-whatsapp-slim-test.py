"""Verify the unpacked Chromium extension has a stable manifest ID."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from base_test import ROOT, fail_check, pass_check


EXTENSION = ROOT / "default/chromium/extensions/whatsapp-slim"
EXPECTED_ID = "amhpgjbcfakkmkeojmoaoiochhifohdi"
ID_ALPHABET = "abcdefghijklmnop"


def extension_id(manifest_path: Path) -> str:
  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  key = base64.b64decode(manifest["key"])
  digest = hashlib.sha256(key).digest()[:16]
  return "".join(ID_ALPHABET[nibble] for byte in digest for nibble in (byte >> 4, byte & 0x0F))


def main() -> int:
  actual_id = extension_id(EXTENSION / "manifest.json")
  if actual_id != EXPECTED_ID:
    fail_check(f"extension manifest retains its stable ID (got {actual_id})")
  pass_check("extension manifest has the stable ID")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
