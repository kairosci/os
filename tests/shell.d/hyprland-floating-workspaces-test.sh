#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/base-test.sh"

# This regression suite guards the removal of floating workspaces and per-app
# floating rules; floating terminal helper names remain for UI layer surfaces.
if rg -n 'float[[:space:]]*=[[:space:]]*true|pin[[:space:]]*=[[:space:]]*true|floating-window|arch-floating-workspace' \
  "$ROOT/default/hypr" "$ROOT/src/cli/arch-hyprland-workspace-layout-"; then
  fail "the window configuration and layout commands contain no floating workspace behavior"
fi
! grep -q 'SUPER + T.*floating' "$ROOT/default/hypr/bindings/tiling.lua" || fail "the floating toggle binding is removed"
! grep -q 'SUPER + O.*pop' "$ROOT/default/hypr/bindings/tiling.lua" || fail "the float and pin binding is removed"
grep -q 'property bool shown: !!dock && fullscreenMode < 2' "$ROOT/src/shell/plugins/dock/DockWindow.qml" || fail "the dock remains available on tiled workspaces"
pass "floating workspace behavior is removed while the dock remains available"
