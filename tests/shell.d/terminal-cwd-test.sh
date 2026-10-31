#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
stub_bin="$test_tmp/bin"
work_dir="$test_tmp/project dir"
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
[[ -n ${ACTIVE_PID:-} ]] && printf 'Window 1 -> terminal:\n\tpid: %s\n' "$ACTIVE_PID"
exit 0
SH
chmod +x "$stub_bin/hyprctl"

cwd=$(ACTIVE_PID="$terminal_pid" PATH="$stub_bin:$PATH" XDG_RUNTIME_DIR="$test_tmp" "$ROOT/src/arch/commands/arch-cmd-terminal-cwd")
[[ $cwd == "$work_dir" ]] || fail "a new terminal opens in the focused terminal's shell directory" "got: $cwd"
pass "a new terminal opens in the focused terminal's shell directory"

output=$(PATH="$stub_bin:$PATH" XDG_RUNTIME_DIR="$test_tmp" HOME="$test_tmp" "$ROOT/src/arch/commands/arch-cmd-terminal-cwd" 2>&1)
[[ $output == "$test_tmp" ]] || fail "with no focused terminal the new one opens in HOME" "got: $output"
pass "with no focused terminal the new one opens in HOME, quietly"

# The Super+Return binding hands over the focused window's pid, so Hyprland is
# not asked again; a hyprctl that fails the test proves it goes unasked.
cat >"$stub_bin/hyprctl" <<'SH'
#!/bin/bash
echo "hyprctl was asked for the active window" >&2
exit 1
SH

cwd=$(PATH="$stub_bin:$PATH" XDG_RUNTIME_DIR="$test_tmp" "$ROOT/src/arch/commands/arch-cmd-terminal-cwd" "$terminal_pid" 2>&1)
[[ $cwd == "$work_dir" ]] || fail "a terminal pid passed in finds its shell directory without hyprctl" "got: $cwd"
pass "a terminal pid passed in finds its shell directory without hyprctl"

cat >"$stub_bin/setsid" <<'SH'
#!/bin/bash
printf '%s\0' "$@" >"$LAUNCH_ARGS"
exit "${LAUNCH_STATUS:-0}"
SH
cat >"$stub_bin/arch-cmd-terminal-cwd" <<'SH'
#!/bin/bash
printf '%s' "$LAUNCH_CWD"
SH
chmod +x "$stub_bin/setsid" "$stub_bin/arch-cmd-terminal-cwd"
launch_args="$test_tmp/launch-args"

AP="$ROOT" PATH="$stub_bin:$PATH" LAUNCH_ARGS="$launch_args" \
  "$ARCH_TEST_CLI_BIN/arch-launch-nautilus" || fail "Files launcher starts successfully"
mapfile -d '' -t actual_args <"$launch_args"
[[ ${#actual_args[@]} == 4 && ${actual_args[0]} == uwsm-app && ${actual_args[1]} == -- &&
  ${actual_args[2]} == nautilus && ${actual_args[3]} == --new-window ]] ||
  fail "Files launcher preserves its application argv" "${actual_args[*]}"

AP="$ROOT" PATH="$stub_bin:$PATH" LAUNCH_ARGS="$launch_args" LAUNCH_CWD="$work_dir" \
  "$ARCH_TEST_CLI_BIN/arch-launch-nautilus-cwd" || fail "Files launcher in the terminal directory starts successfully"
mapfile -d '' -t actual_args <"$launch_args"
[[ ${#actual_args[@]} == 5 && ${actual_args[0]} == uwsm-app && ${actual_args[1]} == -- &&
  ${actual_args[2]} == nautilus && ${actual_args[3]} == --new-window && ${actual_args[4]} == "$work_dir" ]] ||
  fail "Files launcher forwards a path with spaces as one argv item" "${actual_args[*]}"
pass "Files launchers preserve argv and the focused terminal directory"

cat >"$stub_bin/arch-launch-terminal" <<'SH'
#!/bin/bash
printf '%s\0' "$@" >"$LAUNCH_ARGS"
exit "${LAUNCH_STATUS:-0}"
SH
chmod +x "$stub_bin/arch-launch-terminal"
AP="$ROOT" PATH="$stub_bin:$PATH" LAUNCH_ARGS="$launch_args" \
  "$ARCH_TEST_CLI_BIN/arch-launch-terminal-tmux" || fail "tmux terminal launcher starts successfully"
mapfile -d '' -t actual_args <"$launch_args"
[[ ${#actual_args[@]} == 3 && ${actual_args[0]} == bash && ${actual_args[1]} == -c &&
  ${actual_args[2]} == 'tmux attach || tmux new -s Work' ]] ||
  fail "tmux terminal launcher preserves its attach-or-create command" "${actual_args[*]}"
pass "tmux terminal launcher preserves the Work session fallback"
