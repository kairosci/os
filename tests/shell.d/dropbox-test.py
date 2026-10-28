"""Check the Dropbox panel's file and quota model helpers."""

from __future__ import annotations

import subprocess

from base_test import ROOT, fail_check, pass_check, test_environment


model_check = r"""
const assert = require("node:assert/strict")
const dropbox = require(process.cwd() + "/src/arch/shell/plugins/panels/dropbox/Model.js")
assert.equal(dropbox.fileKind("photo.JPG"), "image")
assert.equal(dropbox.fileKind("clip.webm"), "video")
assert.equal(dropbox.fileKind("report.pdf"), "document")
assert.equal(dropbox.fileKind("archive.zip"), "misc")
assert.equal(dropbox.formatBytes(1530), "1.53 KB")
assert.equal(dropbox.formatBytes(2_000_000_000), "2 GB")
assert.equal(dropbox.formatPercent(7.25), "7.3%")
assert.equal(dropbox.usageText(1000, 2000, true), "1 KB of 2 KB")
assert.equal(dropbox.usageText(1000, 0, false), "1 KB")

const parsed = dropbox.parseStatus(JSON.stringify({
  installed: true,
  running: true,
  authenticated: true,
  files: [{ name: "x.txt" }]
}))
assert(parsed.installed && parsed.running && parsed.authenticated)
assert.equal(parsed.files.length, 1)
assert.equal(
  dropbox.fileMeta({ modifiedTs: 1000, folder: "Docs" }, 1000 * 1000 + 3600 * 1000),
  "1h ago · Docs"
)
"""
result = subprocess.run(
  ["node", "-e", model_check],
  capture_output=True,
  text=True,
  cwd=ROOT,
  env=test_environment(),
  check=False,
)
if result.returncode != 0:
  fail_check(f"Dropbox model helpers: {result.stdout}{result.stderr}")
pass_check("Dropbox model helpers preserve file metadata and quota formatting")
