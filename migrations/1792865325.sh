#!/bin/bash

# Move the last OS-named user config, state, and cache directories to Arch names while
# preserving customized files and updating paths in desktop application configs.

set -euo pipefail

merge_directory() {
  local source=$1 target=$2
  [[ -e $source || -L $source ]] || return 0

  mkdir -p "$(dirname "$target")"
  python3 - "$source" "$target" <<'PY'
import filecmp
import os
import stat
import sys

source, target = sys.argv[1:]

def exists(path):
    return os.path.lexists(path)

def same(left, right):
    left_stat = os.lstat(left)
    right_stat = os.lstat(right)
    if stat.S_ISLNK(left_stat.st_mode) and stat.S_ISLNK(right_stat.st_mode):
        return os.readlink(left) == os.readlink(right)
    if stat.S_ISREG(left_stat.st_mode) and stat.S_ISREG(right_stat.st_mode):
        return filecmp.cmp(left, right, shallow=False)
    return False

def legacy_destination(path):
    candidate = path + ".legacy-os"
    suffix = 2
    while exists(candidate):
        candidate = path + f".legacy-os-{suffix}"
        suffix += 1
    return candidate

def merge(src, dst):
    src_stat = os.lstat(src)
    if not exists(dst):
        os.replace(src, dst)
        return

    dst_stat = os.lstat(dst)
    if not stat.S_ISDIR(src_stat.st_mode) or not stat.S_ISDIR(dst_stat.st_mode):
        if same(src, dst):
            if stat.S_ISDIR(src_stat.st_mode):
                os.rmdir(src)
            else:
                os.unlink(src)
        else:
            os.replace(src, legacy_destination(dst))
        return

    with os.scandir(src) as entries:
        for entry in entries:
            merge(entry.path, os.path.join(dst, entry.name))
    os.rmdir(src)

try:
    merge(source, target)
except (OSError, RuntimeError) as error:
    print(f"Could not migrate {source} to {target}: {error}", file=sys.stderr)
    sys.exit(1)
PY
}

config_home=${XDG_CONFIG_HOME:-$HOME/.config}
state_home=${XDG_STATE_HOME:-$HOME/.local/state}
cache_home=${XDG_CACHE_HOME:-$HOME/.cache}

merge_directory "$config_home/os" "$config_home/arch"
merge_directory "$state_home/os" "$state_home/arch"
merge_directory "$cache_home/os" "$cache_home/arch"

# The user menu extension is still loaded at a stable Arch-owned path, while
# the pre-Arch filename came from the old product namespace.
old_menu="$config_home/arch/extensions/arch-menu.jsonc"
new_menu="$config_home/arch/extensions/arch-menu.jsonc"
if [[ -e $old_menu || -L $old_menu ]]; then
  if [[ ! -e $new_menu && ! -L $new_menu ]]; then
    mv "$old_menu" "$new_menu"
  elif cmp -s "$old_menu" "$new_menu"; then
    rm -f "$old_menu"
  else
    legacy_menu="$new_menu.legacy"
    suffix=2
    while [[ -e $legacy_menu || -L $legacy_menu ]]; do
      legacy_menu="$new_menu.legacy-$suffix"
      ((suffix += 1))
    done
    mv "$old_menu" "$legacy_menu"
  fi
fi

python3 - "$config_home" "$state_home/arch" <<'PY'
from pathlib import Path
import sys

roots = [Path(value) for value in sys.argv[1:]]
replacements = (
    (b".config/os", b".config/arch"),
    (b".local/state/os", b".local/state/arch"),
    (b".cache/os", b".cache/arch"),
    (b"config/os/", b"config/arch/"),
)

for root in roots:
    if not root.is_dir():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data:
            continue
        updated = data
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != data:
            path.write_bytes(updated)
PY
