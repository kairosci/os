#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

# The plugin's JS modules, plus Service.qml's admission, close and replay
# functions run against a fake ListModel and fake senders.
require_command node

if output=$(node "$SHELL_TEST_DIR/notifications/logic.cjs" 2>&1); then
  pass "notification logic holds its policies"
else
  fail "notification logic holds its policies" "$output"
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

wait_bin="$tmp/wait-bin"
wait_log="$tmp/wait-log"
mkdir -p "$wait_bin"
cat >"$wait_bin/arch-shell" <<'SH'
#!/bin/bash
printf 'shell\n' >>"$WAIT_LOG"
[[ ${WAIT_SHELL_READY:-0} == 1 ]]
SH
cat >"$wait_bin/busctl" <<'SH'
#!/bin/bash
printf 'bus\n' >>"$WAIT_LOG"
[[ ${WAIT_BUS_READY:-0} == 1 ]]
SH
chmod +x "$wait_bin/arch-shell" "$wait_bin/busctl"

: >"$wait_log"
ARCH_PATH="$ROOT" WAIT_LOG="$wait_log" WAIT_SHELL_READY=1 WAIT_BUS_READY=1 PATH="$wait_bin:$PATH" \
  "$ROOT/src/arch/commands/arch-notification-wait" 1 || fail "notification wait succeeds only after both readiness checks"
[[ $(<"$wait_log") == $'shell\nbus' ]] || fail "notification wait probes the shell before the D-Bus server" "$(<"$wait_log")"
pass "notification wait checks shell IPC and the notification D-Bus name"

: >"$wait_log"
if ARCH_PATH="$ROOT" WAIT_LOG="$wait_log" WAIT_SHELL_READY=1 WAIT_BUS_READY=0 PATH="$wait_bin:$PATH" \
  "$ROOT/src/arch/commands/arch-notification-wait" 1 >/dev/null 2>&1; then
  fail "notification wait times out until the D-Bus server is ready"
fi
grep -q '^bus$' "$wait_log" || fail "notification wait checks D-Bus after shell IPC succeeds" "$(<"$wait_log")"
pass "notification wait times out while the D-Bus server is unavailable"

if LANG=it_IT.UTF-8 ARCH_PATH="$ROOT" "$ROOT/src/arch/commands/arch-notification-wait" invalid >"$tmp/wait-error" 2>&1; then
  fail "notification wait rejects a non-integer timeout"
fi
grep -q 'Il timeout deve essere un intero' "$tmp/wait-error" || fail "notification wait localizes timeout errors" "$(<"$tmp/wait-error")"
pass "notification wait validates and localizes timeout arguments"

if ARCH_PATH="$ROOT" "$ROOT/src/arch/commands/arch-notification-wait" 301 >/dev/null 2>&1; then
  fail "notification wait rejects an excessive timeout"
fi
pass "notification wait enforces the configured maximum timeout"

service="$ROOT/src/arch/shell/plugins/notifications/Service.qml"

# The startup step that makes the state directory, run as the service runs
# it, on a scratch HOME. It must keep the current files, replace a symlinked
# one rather than write through it, and leave the directory and the files the
# shell writes private.
prepare=$(node -e '
  const source = require("node:fs").readFileSync(process.argv[1], "utf8")
  const m = source.match(/id: storePrepare\s+command: \["bash", "-c",([^]*?),\s*"arch-notifications-state"/)
  process.stdout.write(require("node:vm").runInNewContext(m[1]))
' "$service")
state="$tmp/.local/state/arch/notifications"
mkdir -p "$state" "$tmp/outside"
touch "$tmp/outside/keep.json"
echo '[{"key":"n2"}]' >"$state/history.json"
chmod 644 "$state/history.json"
ln -s "$tmp/outside/keep.json" "$state/quiet.json"
bash -c "$prepare" arch-notifications-state "$state" || fail "the state directory is prepared"
left=$(cd "$state" && find . | sort | tr '\n' ' ')
[[ $left == ". ./history.json ./live.json ./quiet.json " ]] || fail "the state files are made" "$left"
[[ -f $tmp/outside/keep.json && $(cat "$state/history.json") == '[{"key":"n2"}]' && ! -L $state/quiet.json && ! -s $state/quiet.json ]] ||
  fail "current state is kept and a symlinked state file replaced"
[[ $(stat -c %a "$state" "$state/live.json" "$state/history.json" "$state/quiet.json" | tr '\n' ' ') == "700 600 600 600 " ]] ||
  fail "the state directory and its files are private"
pass "the state directory is prepared"

# Keybindings and commands call the notifications IPC target by method name.
# Every name they use must be one the service declares, or the key fires into
# "target not found".
declared=$(sed -n '/target: "notifications"/,/^  }/p' "$service" | grep -oE '^    function [A-Za-z]+' | awk '{print $2}' | sort -u)
used=$(
  {
    sed -nE 's/^ipc notifications\.([A-Za-z]+)$/\1/p' "$ROOT/default/arch/shortcuts"
    grep -rhoE 'ipc = "notifications\.[A-Za-z]+"' "$ROOT/default/hypr" | sed -E 's/.*notifications\.([A-Za-z]+)"/\1/'
    grep -rhoE 'arch-shell( -q)? notifications [A-Za-z]+' "$ROOT/src/arch/commands" "$ROOT/installer" | awk '{print $NF}'
  } | sort -u
)
missing=$(comm -13 <(echo "$declared") <(echo "$used"))
[[ -z $missing ]] || fail "every notifications IPC method callers use is declared" "missing: $missing"
pass "every notifications IPC method callers use is declared"

# The surface keeps the namespace the glassy-window layer rule matches.
grep -q 'WlrLayershell.namespace: "arch-notifications"' "$service" ||
  fail "notification surface keeps the arch-notifications layer namespace"
grep -q 'arch-notifications' "$ROOT/default/hypr/toggles/window-glassy.lua" ||
  fail "glassy toggle still matches the notification layer namespace"
pass "notification surface keeps the arch-notifications layer namespace"
