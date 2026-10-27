#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/base-test.sh"
require_command lua

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
mkdir -p "$tmpdir/bin" "$tmpdir/home"
cat >"$tmpdir/bin/hyprctl" <<'STUB'
#!/bin/bash
case "$1" in
  activeworkspace) printf '{"id":3,"tiledLayout":"%s"}\n' "${LAYOUT:-scrolling}" ;;
  getoption) printf '{"str":"%s"}\n' "${LAYOUT:-scrolling}" ;;
  eval) printf '%s\n' "$*" >>"$HYPR_LOG" ;;
  *) printf '%s\n' "$*" >>"$HYPR_LOG" ;;
esac
STUB
cat >"$tmpdir/bin/arch-notification-send" <<'STUB'
#!/bin/bash
printf '%s\n' "$*" >>"$NOTIFY_LOG"
[[ " $* " == *" -p "* ]] && echo 42
STUB
cat >"$tmpdir/bin/arch-i18n" <<'STUB'
#!/bin/bash
printf '%s\n' "$*"
STUB
cat >"$tmpdir/bin/arch-shell" <<'STUB'
#!/bin/bash
printf '%s\n' "$*" >>"$NOTIFY_LOG"
STUB
chmod +x "$tmpdir/bin"/*
export HOME="$tmpdir/home" XDG_STATE_HOME="$tmpdir/home/.local/state"
export PATH="$tmpdir/bin:$ROOT/src/cli:$PATH" HYPR_LOG="$tmpdir/hypr.log" NOTIFY_LOG="$tmpdir/notify.log"

arch-hyprland-workspace-layout-toggle
[[ $(arch-hyprland-workspace-layout-current) == dwindle ]] || fail "the layout cycles from scrolling to tiling"
arch-hyprland-workspace-layout-toggle
[[ ! -e $XDG_STATE_HOME/arch/workspace-layouts/3.lua ]] || fail "the second tiled layout cycles back to default scrolling"
arch-hyprland-workspace-layout-toggle back
[[ $(arch-hyprland-workspace-layout-current) == dwindle ]] || fail "reverse cycling selects tiling"
pass "workspace layout cycling only uses tiled layouts"

mkdir -p "$XDG_STATE_HOME/arch/workspace-layouts"
printf 'o.workspace_mode({ default = "floating" })\n' >"$XDG_STATE_HOME/arch/workspace-layouts/default.lua"
[[ $(arch-hyprland-workspace-layout-default) == scrolling ]] || fail "a legacy floating default is normalized to scrolling"
pass "legacy floating layout state resolves to a tiled default"

if rg -n 'float[[:space:]]*=[[:space:]]*true|pin[[:space:]]*=[[:space:]]*true|floating-window' "$ROOT/default/hypr"; then
  fail "application rules contain no forced floating windows"
fi
grep -q 'tile = true' "$ROOT/default/hypr/windows.lua" || fail "all application windows receive the tiled rule"
! grep -q 'workspace-layout.floating' "$ROOT/default/arch/arch-menu.jsonc" || fail "the menu has no floating layout option"
pass "Hyprland configuration forces application windows to tile"

cat >"$tmpdir/modes.lua" <<'LUA'
local config, rules = {}, {}
hl = {
  config = function(value) for k, v in pairs(value.general) do config[k] = v end end,
  workspace_rule = function(value) table.insert(rules, value) end,
}
o = {}
local modes = dofile(os.getenv("ARCH_PATH") .. "/default/hypr/workspace-modes.lua")
o.workspace_mode({ default = "floating" })
o.workspace_mode({ workspace = "3", mode = "floating" })
modes.apply()
assert(config.layout == "scrolling", "legacy floating default was not normalized")
assert(#rules >= 1 and rules[#rules].workspace == "3" and rules[#rules].layout == "scrolling", "legacy floating workspace was not normalized")
LUA
ARCH_PATH="$ROOT" lua "$tmpdir/modes.lua" || fail "Lua workspace-mode compatibility normalizes legacy modes to scrolling"
pass "workspace layout restoration keeps legacy state tiled"
