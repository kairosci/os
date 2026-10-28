# ISO release assets

GitHub release assets must stay below 2 GB. The ISO release helper uses a 1,900,000,000-byte default part size and publishes a JSON manifest with the size and SHA-256 checksum of the complete ISO and every part.

Split an ISO into assets for a release:

```sh
python3 scripts/iso/parts.py split arch-4.0.6.iso --output-dir release-assets
```

Upload a built ISO to an existing GitHub release. The helper creates the parts and manifest, then uploads them together:

```sh
python3 scripts/iso/upload.py arch-4.0.6.iso v4.0.6 --repo kairosci/os
```

Keep the manifest with the parts; the downloader uses it to select assets and verify their contents.

Download, verify, and assemble an ISO from a release:

```sh
python3 scripts/iso/download.py v4.0.6 --repo kairosci/os --output-dir .
```

The downloader requires the GitHub CLI to be authenticated for the selected repository. To assemble already-downloaded assets without network access:

```sh
python3 scripts/iso/parts.py assemble release-assets/arch-4.0.6.iso.parts.json --output-dir .
```

Assembly checks each part's expected name, byte count, and SHA-256 checksum, then checks the complete ISO before publishing the destination with an atomic rename. It refuses to overwrite an existing ISO. The manifest format is versioned so future release tooling can reject unsupported layouts instead of producing a truncated image.
