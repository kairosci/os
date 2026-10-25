#!/bin/bash

set -euo pipefail

session_dir=${ARCH_WAYLAND_SESSIONS_DIR:-/usr/local/share/wayland-sessions}
source="$ARCH_PATH/default/wayland-sessions/arch.desktop"

[[ -f $source ]] || {
  echo "Arch Wayland session entry is missing: $source" >&2
  exit 1
}

sudo install -Dm644 "$source" "$session_dir/arch.desktop"
for entry in "$session_dir"/*archy.desktop; do
  [[ -e $entry ]] || continue
  [[ $entry == "$session_dir/arch.desktop" ]] && continue
  sudo rm -f "$entry"
done
