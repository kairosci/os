#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/base-test.sh"

# This regression suite guards the removal of floating workspaces and per-app
# floating rules; floating terminal helper names remain for UI layer surfaces.
if rg -n 'float[[:space:]]*=[[:space:]]*true|pin[[:space:]]*=[[:space:]]*true|floating-window|arch-floating-workspace' \
  "$ROOT/default/hypr" "$ROOT/src/cli/arch-hyprland-workspace-layout-current" \
  "$ROOT/src/cli/arch-hyprland-workspace-layout-default" \
  "$ROOT/src/cli/arch-hyprland-workspace-layout-toggle"; then
  fail "the window configuration and layout commands contain no floating workspace behavior"
fi
! grep -q 'SUPER + T.*floating' "$ROOT/default/hypr/bindings/tiling.lua" || fail "the floating toggle binding is removed"
! grep -q 'SUPER + O.*pop' "$ROOT/default/hypr/bindings/tiling.lua" || fail "the float and pin binding is removed"
[[ ! -e $ROOT/src/cli/arch-hyprland-window-pop ]] || fail "the float and pin command is removed"
! grep -q 'arch-hyprland-window-pop' "$ROOT/modules/desktop/commands/hyprland/module.toml" || fail "the float and pin command is not packaged"
grep -q 'property bool shown: !!dock && fullscreenMode < 2' "$ROOT/src/shell/plugins/dock/DockWindow.qml" || fail "the dock remains available on tiled workspaces"
grep -q 'arch-pkg-drop arch-hyprland-titlebars' "$ROOT/migrations/1792938567.sh" || fail "old floating titlebars are removed from installed systems"
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
mkdir -p "$tmpdir/bin"
cat >"$tmpdir/bin/arch-pkg-drop" <<'STUB'
#!/bin/bash
printf '%s\n' "$*" >>"$MIGRATION_LOG"
STUB
chmod +x "$tmpdir/bin/arch-pkg-drop"
MIGRATION_LOG="$tmpdir/packages.log" PATH="$tmpdir/bin:$PATH" bash "$ROOT/migrations/1792938567.sh" >/dev/null
grep -qx 'arch-hyprland-titlebars' "$tmpdir/packages.log" || fail "the migration removes the obsolete titlebar package"
pass "floating workspace behavior is removed while the dock remains available"
