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
export AP="$ROOT" PATH="$tmpdir/bin:$ARCH_TEST_CLI_BIN:$ROOT/src/arch/commands:$PATH" HYPR_LOG="$tmpdir/hypr.log" NOTIFY_LOG="$tmpdir/notify.log"

arch-hyprland-workspace-layout-toggle
[[ $(archctl hyprland workspace layout current) == tiling ]] || fail "the layout cycles from scrolling to tiling"
arch-hyprland-workspace-layout-toggle
[[ ! -e $XDG_STATE_HOME/arch/workspace-layouts/3.lua ]] || fail "the second tiled layout cycles back to default scrolling"
arch-hyprland-workspace-layout-toggle back
[[ $(archctl hyprland workspace layout current) == tiling ]] || fail "reverse cycling selects tiling"
pass "workspace layout cycling only uses tiled layouts"

mkdir -p "$XDG_STATE_HOME/arch/workspace-layouts"
printf 'o.workspace_mode({ default = "unknown" })\n' >"$XDG_STATE_HOME/arch/workspace-layouts/default.lua"
[[ $(arch-hyprland-workspace-layout-default) == scrolling ]] || fail "an unknown saved mode falls back to scrolling"
pass "workspace layout state accepts only the configured modes"

grep -q 'tile = true' "$ROOT/default/hypr/windows.lua" || fail "all application windows receive the tiled rule"
grep -q 'appearance.workspace-layout.scrolling' "$ROOT/default/arch/arch-menu.jsonc" || fail "scrolling remains in the layout menu"
grep -q 'appearance.workspace-layout.tiling' "$ROOT/default/arch/arch-menu.jsonc" || fail "tiling remains in the layout menu"
pass "Hyprland configuration offers scrolling and tiling layouts"

cat >"$tmpdir/modes.lua" <<'LUA'
local config, rules = {}, {}
hl = {
  config = function(value) for k, v in pairs(value.general) do config[k] = v end end,
  workspace_rule = function(value) table.insert(rules, value) end,
}
o = {}
local modes = dofile(os.getenv("AP") .. "/default/hypr/workspace-modes.lua")
o.workspace_mode({ default = "unknown" })
o.workspace_mode({ workspace = "3", mode = "unknown" })
modes.apply()
assert(config.layout == "scrolling", "unknown defaults must retain scrolling")
assert(#rules == 0, "unknown per-workspace modes must not add compositor rules")
LUA
AP="$ROOT" lua "$tmpdir/modes.lua" || fail "workspace-mode validation must ignore unknown modes safely"
pass "workspace layout restoration accepts only scrolling and tiling"
