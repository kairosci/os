#!/bin/bash

set -euo pipefail

python3 - "${ARCH_LIMINE_CONF:-/boot/limine.conf}" "${ARCH_SYSTEMD_BOOT_ESP:-/boot}" <<'PY'
import os
import pathlib
import re
import sys
import tempfile

config_path = pathlib.Path(sys.argv[1])
esp_path = pathlib.Path(sys.argv[2])
entries_path = esp_path / "loader/entries"

try:
    lines = config_path.read_text(encoding="utf-8").splitlines()
except OSError as error:
    raise SystemExit(f"Cannot read {config_path}: {error}")

in_snapshots = False
snapshot_seen = False
snapshot_number = ""
snapshot_date = ""
kernel_name = ""
uki_path = ""
kernel_options = ""
generated = {}


def finish_entry():
    if not (snapshot_number and kernel_name and uki_path and kernel_options):
        return

    match = re.fullmatch(r"boot\(\):(/[^#]+)(?:#([0-9a-fA-F]+))?", uki_path)
    if not match:
        return

    relative_uki = match.group(1)
    image_path = esp_path / relative_uki.lstrip("/")
    if not image_path.is_file():
        return

    if kernel_name == "linux":
        kernel_label = "Arch Linux"
        kernel_slug = "arch"
    elif kernel_name.startswith("linux"):
        kernel_label = "Recovery kernel"
        kernel_slug = "recovery"
    elif kernel_name.startswith("linux-t2"):
        kernel_label = "T2 kernel"
        kernel_slug = "t2"
    else:
        kernel_label = re.sub(r"[^A-Za-z0-9 ._-]", "", kernel_name).replace("-", " ")
        kernel_slug = re.sub(r"[^a-z0-9-]", "-", kernel_name.lower()).strip("-") or "kernel"

    snapshot_label = f"Snapshot #{snapshot_number}"
    if snapshot_date:
        snapshot_label += f" ({snapshot_date})"
    title = f"{snapshot_label} - {kernel_label}"
    filename = f"arch-snapshot-{snapshot_number}-{kernel_slug}.conf"
    machine_id = relative_uki.strip("/").split("/", 1)[0]
    content = [f"title   {title}", "sort-key snapshots", f"uki     {relative_uki}"]
    content.append(f"options {kernel_options}")
    generated[filename] = "\n".join(content) + "\n"


for raw_line in lines:
    line = raw_line.strip()
    if line == "//Snapshots":
        snapshot_seen = True
        in_snapshots = True
        continue
    if not in_snapshots:
        continue
    if line.startswith("/") and not line.startswith("///"):
        finish_entry()
        in_snapshots = False
        continue

    snapshot_match = re.fullmatch(r"///(\d+)\s+│\s*(.*)", line)
    if snapshot_match:
        finish_entry()
        snapshot_number, snapshot_date = snapshot_match.groups()
        kernel_name = ""
        uki_path = ""
        kernel_options = ""
        continue

    kernel_match = re.fullmatch(r"////([A-Za-z0-9_.+-]+)", line)
    if kernel_match:
        finish_entry()
        kernel_name = kernel_match.group(1)
        uki_path = ""
        kernel_options = ""
        continue

    if line.startswith("path:"):
        uki_path = line.partition(":")[2].strip()
    elif line.startswith("cmdline:"):
        kernel_options = line.partition(":")[2].strip()

finish_entry()

if not snapshot_seen:
    raise SystemExit(f"No Snapper snapshot section in {config_path}; existing entries were left alone.")

entries_path.mkdir(parents=True, exist_ok=True)
for filename, content in generated.items():
    fd, temporary = tempfile.mkstemp(prefix=f".{filename}.", dir=entries_path, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as entry_file:
            entry_file.write(content)
        os.chmod(temporary, 0o644)
        os.replace(temporary, entries_path / filename)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

for stale_entry in entries_path.glob("arch-snapshot-*.conf"):
    if stale_entry.name not in generated:
        stale_entry.unlink()

print(f"Wrote {len(generated)} systemd-boot snapshot entr{'y' if len(generated) == 1 else 'ies'}.")
PY
