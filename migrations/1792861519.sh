#!/bin/bash

# Move user-owned settings and runtime state into Arch-named home directories.
# Identical files are deduplicated; conflicting files are kept beside the Arch
# copy with a .legacy-arch suffix.

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
    candidate = path + ".legacy-arch"
    suffix = 2
    while exists(candidate):
        candidate = path + f".legacy-arch-{suffix}"
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

merge_directory "$config_home/arch" "$config_home/arch"
merge_directory "$state_home/arch" "$state_home/arch"
merge_directory "${XDG_CACHE_HOME:-$HOME/.cache}/arch" "${XDG_CACHE_HOME:-$HOME/.cache}/arch"
