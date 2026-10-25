#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

test_root="$test_tmp/source"
session_dir="$test_tmp/sessions"
mkdir -p "$test_root/default/wayland-sessions" "$session_dir" "$test_tmp/bin"
cp "$ROOT/default/wayland-sessions/arch.desktop" "$test_root/default/wayland-sessions/arch.desktop"
printf '%s\n' '[Desktop Entry]' 'Name=Old Arch Session' >"$session_dir/arch.desktop"

cat >"$test_tmp/bin/sudo" <<'SH'
#!/bin/bash
exec "$@"
SH
chmod +x "$test_tmp/bin/sudo"

PATH="$test_tmp/bin:$PATH" ARCH_PATH="$test_root" \
ARCH_WAYLAND_SESSIONS_DIR="$session_dir" \
  bash "$ROOT/migrations/1792868000.sh"

[[ -f $session_dir/arch.desktop ]] || fail "the Arch session entry is installed"
grep -Fxq 'Name=Arch Linux (Hyprland)' "$session_dir/arch.desktop" ||
  fail "the display manager shows Arch as the session name"
[[ ! -e $session_dir/arch.desktop ]] || fail "the old Arch session entry is removed"
pass "the Wayland session is renamed from Arch to Arch"

PATH="$test_tmp/bin:$PATH" ARCH_PATH="$test_root" \
ARCH_WAYLAND_SESSIONS_DIR="$session_dir" \
  bash "$ROOT/migrations/1792868000.sh"
pass "the Wayland session rename is idempotent"
