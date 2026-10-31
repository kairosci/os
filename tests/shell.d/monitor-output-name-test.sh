#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

require_command jq

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

stub_dir="$tmpdir/bin"
home_dir="$tmpdir/home"
monitors_json="$tmpdir/monitors.json"
flag_dir="$home_dir/.local/state/arch/toggles/hypr"
mkdir -p "$stub_dir" "$flag_dir"

make_stub() {
  local name=$1
  local body=$2
  printf '#!/bin/bash\n%s\n' "$body" >"$stub_dir/$name"
  chmod +x "$stub_dir/$name"
}

make_stub arch-notification-send ':'
make_stub arch-hyprland-monitor-internal ':'
make_stub arch-hyprland-monitor-internal-mirror ':'
make_stub archctl 'if [[ ${1:-} == notification && ${2:-} == send ]]; then
  shift 2
  notification_command=$(command -v arch-notification-send) || exit 127
  exec "$notification_command" "$@"
fi
if [[ ${1:-} == hyprland && ${2:-} == toggle ]]; then
  exit 0
fi
case "$*" in
  "hyprland monitor laptop") printf "%s\n" "$LAPTOP_NAME" ;;
  "hyprland monitor external active") exec "$ROOT/src/arch/commands/archctl" "$@" ;;
  "hw clamshell") exit 0 ;;
esac'
make_stub hyprctl 'case "$1" in
  monitors) cat "$MONITORS_JSON" ;;
  eval) printf "%s\n" "$2" >>"$EVAL_LOG" ;;
esac'

eval_log="$tmpdir/eval.log"

run_monitor() {
  local command=$1
  shift
  : >"$eval_log"
  HOME="$home_dir" \
    XDG_STATE_HOME="$home_dir/.local/state" \
    LAPTOP_NAME="${LAPTOP_NAME:-eDP-1}" \
    MONITORS_JSON="$monitors_json" \
    EVAL_LOG="$eval_log" \
    PATH="$stub_dir:$ARCH_TEST_CLI_ROUTER:$ROOT/src/arch/commands:$PATH" \
    "$ROOT/src/arch/commands/$command" "$@"
}

run_external_active() {
  AP="$ROOT" \
  MONITORS_JSON="$monitors_json" \
  PATH="$stub_dir:$PATH" \
    archctl hyprland monitor external active
}

printf '[{"name":"eDP-1"},{"name":"DP-3"}]\n' >"$monitors_json"

disable_flag="$flag_dir/internal-monitor-disable.lua"
run_monitor arch-hyprland-monitor-internal off
grep -Fx 'hl.monitor({ output = "eDP-1", disabled = true })' "$disable_flag" >/dev/null ||
  fail "internal off writes the connector name into the toggle flag"
pass "internal off accepts a plain connector name"

rm -f "$disable_flag"
set +e
LAPTOP_NAME='eDP-1", disabled = false })os.execute("calc")--' \
  run_monitor arch-hyprland-monitor-internal off >/dev/null 2>&1
status=$?
set -e
(( status != 0 )) || fail "internal off rejects a monitor name with Lua metacharacters"
[[ ! -e $disable_flag ]] || fail "an unsafe monitor name is not written as Lua"
pass "internal off refuses an unsafe monitor name"

mirror_flag="$flag_dir/internal-monitor-mirror.lua"
run_monitor arch-hyprland-monitor-internal-mirror on
grep -Fx 'hl.monitor({ output = "DP-3", mode = "preferred", position = "auto", scale = 1, mirror = "eDP-1" })' \
  "$mirror_flag" >/dev/null ||
  fail "mirror on writes the connector names into the toggle flag"
pass "mirror on accepts plain connector names"

rm -f "$mirror_flag"
printf '[{"name":"eDP-1"},{"name":"HEAD\\" })os.execute(\\"calc\\")--"}]\n' >"$monitors_json"
set +e
run_monitor arch-hyprland-monitor-internal-mirror on >/dev/null 2>&1
status=$?
set -e
(( status != 0 )) || fail "mirror on rejects an external name with Lua metacharacters"
[[ ! -e $mirror_flag ]] || fail "an unsafe external monitor name is not written as Lua"
pass "mirror on refuses an unsafe headless output name"

# The clamshell sync writes the internal-monitor name into generated Lua too.
clamshell_flag="$flag_dir/internal-monitor-clamshell.lua"
printf '[{"name":"eDP-1"}]\n' >"$monitors_json"
rm -f "$clamshell_flag"
run_monitor arch-hyprland-monitor-clamshell
grep -Fx 'hl.monitor({ output = "eDP-1", disabled = true })' "$clamshell_flag" >/dev/null ||
  fail "clamshell disable writes the connector name into the toggle flag"
pass "clamshell disable accepts a plain connector name"

rm -f "$clamshell_flag"
set +e
LAPTOP_NAME='eDP-1", disabled = true })os.execute("calc")--' \
  run_monitor arch-hyprland-monitor-clamshell >/dev/null 2>&1
status=$?
set -e
(( status != 0 )) || fail "clamshell rejects a monitor name with Lua metacharacters"
[[ ! -e $clamshell_flag ]] || fail "an unsafe internal monitor name is not written as clamshell Lua"
pass "clamshell refuses an unsafe internal monitor name"

# The scaling command eval's the focused-monitor name into a Lua string.
printf '[{"name":"eDP-1","focused":true,"scale":1.0,"width":1920,"height":1080,"refreshRate":60.0}]\n' \
  >"$monitors_json"
run_monitor arch-hyprland-monitor-scaling 1.6
grep -F 'hl.monitor({ output = "eDP-1"' "$eval_log" >/dev/null ||
  fail "scaling eval's the focused connector name"
pass "scaling accepts a plain connector name"

printf '[{"name":"eDP-1\\" })os.execute(\\"calc\\")--","focused":true,"scale":1.0,"width":1920,"height":1080,"refreshRate":60.0}]\n' \
  >"$monitors_json"
set +e
run_monitor arch-hyprland-monitor-scaling 1.6 >/dev/null 2>&1
status=$?
set -e
(( status != 0 )) || fail "scaling rejects a focused monitor name with Lua metacharacters"
[[ ! -s $eval_log ]] || fail "an unsafe focused monitor name is not eval'd as Lua"
pass "scaling refuses an unsafe focused monitor name"

printf '[{"name":"eDP-1","disabled":false},{"name":"DP-3","disabled":false}]\n' >"$monitors_json"
run_external_active || fail "an active external display is detected"
pass "an active external display is detected"

printf '[{"name":"eDP-1","disabled":false},{"name":"DP-3","disabled":true}]\n' >"$monitors_json"
if run_external_active; then fail "a disabled external display is not active"; fi
pass "a disabled external display is not active"

printf '[{"name":"eDP-1","disabled":false}]\n' >"$monitors_json"
if run_external_active; then fail "an active internal display is not external"; fi
pass "an active internal display is not external"
