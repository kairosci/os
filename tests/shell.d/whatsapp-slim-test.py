#!/usr/bin/python3

"""Verify the slim browser extension follows the system theme."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

from base_test import ROOT, fail_check, pass_check


EXTENSION = ROOT / "default/chromium/extensions/whatsapp-slim"


def main() -> int:
  manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))
  content_script = manifest["content_scripts"][0]
  if content_script.get("js") != ["system-theme.js"] or content_script.get("run_at") != "document_start":
    fail_check("WhatsApp enables system theming before startup")
  pass_check("WhatsApp enables system theming before startup")

  node = shutil.which("node")
  if node is None:
    fail_check("Node.js is available for the extension runtime check")
  harness = """
const fs = require("fs")
const values = new Map()
let reloaded = false
global.localStorage = {
  getItem: key => values.get(key),
  setItem: (key, value) => values.set(key, value),
}
global.location = { reload: () => { reloaded = true } }
eval(fs.readFileSync(process.argv[1], "utf8"))
process.stdout.write(`${values.get("system-theme-mode")}:${reloaded}`)
"""
  result = subprocess.run(
    [node, "-e", harness, str(EXTENSION / "system-theme.js")],
    check=False,
    capture_output=True,
    text=True,
  )
  if result.returncode != 0 or result.stdout != "true:true":
    fail_check("WhatsApp follows the system theme through its existing slim extension")
  pass_check("WhatsApp follows the system theme through its existing slim extension")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
