#!/bin/bash

set -euo pipefail

action="${1:-}"
subvolume="${2:-}"
snapshot_id="${4:-}"
boot_root="${ARCH_SNAPSHOTS_BOOT_ROOT:-/boot}"
snapshots_root="${ARCH_SNAPSHOTS_ROOT:-/.snapshots}"
machine_id="${ARCH_MACHINE_ID:-$(< /etc/machine-id)}"
arch_uki="${ARCH_ARCH_UKI:-$boot_root/EFI/Linux/os_linux.efi}"
archive_dir="$boot_root/$machine_id/arch-snapshots"
entries_dir="$boot_root/loader/entries"
systemd_unit_dir="${ARCH_SYSTEMD_UNIT_DIR:-/etc/systemd/system}"
systemd_libexec_dir="${ARCH_SYSTEMD_LIBEXEC_DIR:-/usr/local/libexec}"
limine_snapper_plugin="${ARCH_LIMINE_SNAPPER_PLUGIN:-/usr/lib/snapper/plugins/10-limine-snapper-sync}"

[[ $subvolume == "/" ]] || exit 0
[[ $snapshot_id =~ ^[0-9]+$ ]] || exit 0
case "$action" in
  create-snapshot-post)
    [[ -d $snapshots_root/$snapshot_id/snapshot && -s $arch_uki ]] || exit 0
    ;;
  delete-snapshot-post)
    ;;
  *)
    exit 0
    ;;
esac
if ! bootctl status --no-pager 2>/dev/null | grep -Eq '^[[:space:]]*Product: systemd-boot([[:space:]]|$)'; then
  exit 0
fi

# Stop the Limine-backed converter only after systemd-boot has actually booted.
systemctl disable --now limine-snapper-sync.service >/dev/null 2>&1 || true
chmod a-x "$limine_snapper_plugin" 2>/dev/null || true
systemctl disable --now arch-snapshot-entries.path arch-snapshot-entries.service >/dev/null 2>&1 || true
rm -f -- "$systemd_unit_dir/arch-snapshot-entries.path" \
  "$systemd_unit_dir/arch-snapshot-entries.service" \
  "$systemd_libexec_dir/arch-sync-systemd-boot-snapshots"
systemctl daemon-reload

snapshot_dir="$snapshots_root/$snapshot_id/snapshot"
snapshot_info="$snapshots_root/$snapshot_id/info.xml"
snapshot_uki="$archive_dir/snapshot-$snapshot_id-linux.efi"
snapshot_entry="$entries_dir/arch-snapshot-$snapshot_id.conf"

case "$action" in
  create-snapshot-post)
    mkdir -p "$archive_dir" "$entries_dir"

    cmdline_file=$(mktemp)
    uki_file=$(mktemp "$archive_dir/.snapshot-$snapshot_id.XXXXXX.efi")
    trap 'rm -f -- "$cmdline_file" "$uki_file"' EXIT
    objcopy -O binary --only-section=.cmdline "$arch_uki" "$cmdline_file"
    python3 - "$cmdline_file" "$snapshot_id" <<'PY'
import pathlib
import sys

cmdline_path = pathlib.Path(sys.argv[1])
snapshot_id = sys.argv[2]
cmdline = cmdline_path.read_text(encoding="utf-8").rstrip("\0\n ")
tokens = cmdline.split()
rootflags_found = False
for index, token in enumerate(tokens):
    if token.startswith("rootflags="):
        rootflags_found = True
        flags = token.removeprefix("rootflags=").split(",")
        flags = [flag for flag in flags if not flag.startswith("subvol=") and not flag.startswith("subvolid=")]
        tokens[index] = "rootflags=" + ",".join([f"subvol=@/.snapshots/{snapshot_id}/snapshot", *flags])
        break

if not rootflags_found:
    raise SystemExit("The Arch UKI command line has no rootflags= option; refusing to build a snapshot UKI.")

cmdline_path.write_text(" ".join(tokens) + "\0", encoding="utf-8")
PY
    cp -- "$arch_uki" "$uki_file"
    objcopy --update-section ".cmdline=$cmdline_file" "$uki_file"
    chmod 0644 "$uki_file"
    mv -f -- "$uki_file" "$snapshot_uki"

    snapshot_date=$(python3 - "$snapshot_info" <<'PY'
import datetime
import pathlib
import sys
import xml.etree.ElementTree as ET

try:
    root = ET.parse(pathlib.Path(sys.argv[1])).getroot()
    stamp = root.findtext("date", "")
    parsed = datetime.datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")
    print(parsed.strftime("%Y-%m-%d %H:%M:%S"))
except (OSError, ValueError, ET.ParseError):
    print("")
PY
)
    title="Snapshot #$snapshot_id"
    [[ -n $snapshot_date ]] && title+=" ($snapshot_date)"
    temporary_entry=$(mktemp "$entries_dir/.arch-snapshot-$snapshot_id.XXXXXX")
    printf 'title   %s - Arch Linux\nsort-key snapshots\nuki     /%s/arch-snapshots/snapshot-%s-linux.efi\n' \
      "$title" "$machine_id" "$snapshot_id" >"$temporary_entry"
    chmod 0644 "$temporary_entry"
    mv -f -- "$temporary_entry" "$snapshot_entry"
    rm -f -- "$entries_dir/arch-snapshot-$snapshot_id-arch.conf" \
      "$entries_dir/arch-snapshot-$snapshot_id-recovery.conf"
    ;;
  delete-snapshot-post)
    rm -f -- "$snapshot_entry" "$snapshot_uki" \
      "$entries_dir/arch-snapshot-$snapshot_id-arch.conf" \
      "$entries_dir/arch-snapshot-$snapshot_id-recovery.conf"
    ;;
  *)
    exit 0
    ;;
esac
