#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
stub_bin="$test_tmp/bin"
work_dir="$test_tmp/project dir"
launch_args="$test_tmp/launch-args"
mkdir -p "$stub_bin" "$work_dir"

# A stand-in terminal whose newest child is a shell sitting in work_dir. The
# trailing ":" keeps bash from exec'ing sleep, so the child stays a shell.
bash -c '(cd "$1" && bash -c "sleep 30; :") & wait' _ "$work_dir" &
terminal_pid=$!

# Children first: killing a parent reparents its children out of reach.
kill_tree() {
  local child
  for child in $(cat /proc/"$1"/task/*/children 2>/dev/null); do
    kill_tree "$child"
  done
  kill "$1" 2>/dev/null || true
}
trap 'kill_tree "$terminal_pid"; wait "$terminal_pid" 2>/dev/null || true; rm -rf "$test_tmp"' EXIT

for _ in $(seq 50); do
  [[ -n $(cat /proc/"$terminal_pid"/task/*/children 2>/dev/null) ]] && break
  sleep 0.05
done

cat >"$stub_bin/hyprctl" <<'SH'
#!/bin/bash
[[ ${1:-} == activewindow && -n ${ACTIVE_PID:-} ]] || exit 0
printf 'Window 1 -> terminal:\n\tpid: %s\n' "$ACTIVE_PID"
SH
cat >"$stub_bin/setsid" <<'SH'
#!/bin/bash
printf '%s\0' "$@" >"$LAUNCH_ARGS"
exit "${LAUNCH_STATUS:-0}"
SH
chmod +x "$stub_bin/hyprctl" "$stub_bin/setsid"

AP="$ROOT" ACTIVE_PID="$terminal_pid" PATH="$stub_bin:$PATH" XDG_RUNTIME_DIR="$test_tmp" \
  HOME="$test_tmp" LAUNCH_ARGS="$launch_args" "$ARCH_TEST_CLI_BIN/archctl" launch terminal ||
  fail "a new terminal starts in the focused terminal shell directory"
mapfile -d '' -t actual_args <"$launch_args"
[[ ${#actual_args[@]} == 4 && ${actual_args[0]} == uwsm-app && ${actual_args[1]} == -- &&
  ${actual_args[2]} == xdg-terminal-exec && ${actual_args[3]} == "--dir=$work_dir" ]] ||
  fail "terminal launch preserves the focused shell directory as one argument" "${actual_args[*]}"
pass "a new terminal opens in the focused terminal shell directory"

: >"$launch_args"
AP="$ROOT" PATH="$stub_bin:$PATH" XDG_RUNTIME_DIR="$test_tmp" HOME="$test_tmp" \
  LAUNCH_ARGS="$launch_args" "$ARCH_TEST_CLI_BIN/archctl" launch terminal ||
  fail "a terminal starts in HOME when there is no focused terminal"
mapfile -d '' -t actual_args <"$launch_args"
[[ ${actual_args[3]} == "--dir=$test_tmp" ]] ||
  fail "a missing focused terminal falls back to HOME" "${actual_args[*]}"
pass "a missing focused terminal falls back to HOME"

cat >"$stub_bin/hyprctl" <<'SH'
#!/bin/bash
echo "hyprctl was asked for the active window" >&2
exit 1
SH
chmod +x "$stub_bin/hyprctl"
: >"$launch_args"
AP="$ROOT" PATH="$stub_bin:$PATH" XDG_RUNTIME_DIR="$test_tmp" HOME="$test_tmp" \
  LAUNCH_ARGS="$launch_args" "$ARCH_TEST_CLI_BIN/archctl" launch terminal "--pid=$terminal_pid" ||
  fail "a terminal pid supplied by the binding starts successfully"
mapfile -d '' -t actual_args <"$launch_args"
[[ ${actual_args[3]} == "--dir=$work_dir" ]] ||
  fail "a supplied terminal pid avoids querying Hyprland and preserves its directory" "${actual_args[*]}"
pass "a supplied terminal pid avoids querying Hyprland"

: >"$launch_args"
AP="$ROOT" PATH="$stub_bin:$PATH" XDG_RUNTIME_DIR="$test_tmp" HOME="$test_tmp" \
  LAUNCH_ARGS="$launch_args" "$ARCH_TEST_CLI_BIN/archctl" launch nautilus cwd ||
  fail "Files launches in the active terminal directory"
mapfile -d '' -t actual_args <"$launch_args"
[[ ${#actual_args[@]} == 5 && ${actual_args[0]} == uwsm-app && ${actual_args[1]} == -- &&
  ${actual_args[2]} == nautilus && ${actual_args[3]} == --new-window && ${actual_args[4]} == "$work_dir" ]] ||
  fail "Files launcher forwards a path with spaces as one argv item" "${actual_args[*]}"
pass "Files launcher preserves argv and the focused terminal directory"

: >"$launch_args"
AP="$ROOT" PATH="$stub_bin:$PATH" XDG_RUNTIME_DIR="$test_tmp" HOME="$test_tmp" \
  LAUNCH_ARGS="$launch_args" "$ARCH_TEST_CLI_BIN/archctl" launch terminal tmux ||
  fail "tmux starts in a tiled terminal"
mapfile -d '' -t actual_args <"$launch_args"
[[ ${#actual_args[@]} == 7 && ${actual_args[2]} == xdg-terminal-exec &&
  ${actual_args[3]} == "--dir=$test_tmp" && ${actual_args[4]} == bash &&
  ${actual_args[5]} == -c && ${actual_args[6]} == 'tmux attach || tmux new -s Work' ]] ||
  fail "tmux terminal launcher preserves the Work session command" "${actual_args[*]}"
pass "tmux terminal launcher preserves its attach-or-create command"
