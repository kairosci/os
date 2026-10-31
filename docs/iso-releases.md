# ISO release assets

GitHub release assets must stay below 2 GB. The release workflow builds each supported native architecture in its pinned Arch container, validates the ISO profile, and splits the resulting image into parts no larger than the configured limit. It publishes a JSON manifest with the size and SHA-256 checksum of the complete ISO and every part. The ISO build is restricted to that workflow; local commands only split existing images or download and assemble published ones. A manual workflow run builds a selected ref and stores a short-lived artifact without publishing by default; publishing requires an explicit option and an existing tag.

The profile source is Python in `scripts/iso/profile/profiledef.py`; its values come from `data/iso/profile.yml`. During the CI build it renders a temporary `profiledef.sh`, the profile filename required by ArchISO's profile format ([profile documentation](https://github.com/archlinux/archiso/blob/master/docs/README.profile.rst)). The generated file is confined to the staged build profile and is not checked into the repository.

Split an ISO into assets for a release:

```sh
archctl iso parts split arch-4.0.6.iso --output-dir release-assets
```

The release workflow uploads the parts and manifest together. Keep the manifest with the parts; the downloader uses it to select assets and verify their contents.

Download, verify, and assemble an ISO from a release:

```sh
archctl iso download v4.0.6 --repo kairosci/os --output-dir .
```

The downloader requires the GitHub CLI to be authenticated for the selected repository. To assemble already-downloaded assets without network access:

```sh
archctl iso parts assemble release-assets/arch-4.0.6.iso.parts.json --output-dir .
```

Upload an existing ISO to an existing release with the GitHub CLI:

```sh
archctl iso upload arch-4.0.6.iso v4.0.6 --repo kairosci/os
```

Assembly checks each part's expected name, byte count, and SHA-256 checksum, then checks the complete ISO before publishing the destination with an atomic rename. It refuses to overwrite an existing ISO. The manifest format is versioned so future release tooling can reject unsupported layouts instead of producing a truncated image.
