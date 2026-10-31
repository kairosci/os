#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

fake_bin="$test_tmp/bin"
mkdir -p "$fake_bin"

cat >"$fake_bin/hyprctl" <<'SH'
#!/bin/bash

[[ ${1:-} == "-j" && ${2:-} == "monitors" ]] || exit 1
[[ ${ARCH_TEST_HYPRCTL_FAILS:-0} == 1 ]] && exit 4
if [[ ${ARCH_TEST_HYPRCTL_MODE:-} == "slow" ]]; then
  exec sleep 10
elif [[ ${ARCH_TEST_HYPRCTL_MODE:-} == "large" ]]; then
  exec head -c 256 /dev/zero
fi
printf '%s\n' "$ARCH_TEST_MONITORS"
SH
chmod +x "$fake_bin/hyprctl"

test_ap="$test_tmp/ap"
mkdir -p "$test_ap/data/cli"
ln -s "$ROOT/src" "$test_ap/src"
cat >"$test_ap/data/cli/hyprland-session-locked.yml" <<EOF
command: ['$fake_bin/hyprctl', -j, monitors]
timeout_seconds: 1
cleanup_timeout_seconds: 1
max_output_bytes: 262144
read_chunk_bytes: 4
fields:
  blockers: solitaryBlockedBy
blockers:
  lock: LOCK
  workspace: WORKSPACE
statuses:
  locked: 0
  unlocked: 1
  undetermined: 2
EOF

LOCKED=0
UNLOCKED=1
UNDETERMINED=2

assert_status() {
  local expected="$1" monitors="$2" description="$3" hyprctl_fails="${4:-0}" actual=0

  AP="$test_ap" PATH="$fake_bin:$ARCH_TEST_CLI_BIN:$PATH" \
  ARCH_TEST_MONITORS="$monitors" \
  ARCH_TEST_HYPRCTL_FAILS="$hyprctl_fails" \
    "$ARCH_TEST_CLI_BIN/arch-hyprland-session-locked" || actual=$?

  (( actual == expected )) || fail "$description" "expected exit $expected, got $actual"
  pass "$description"
}

# LOCK in solitaryBlockedBy is how an active ext-session-lock shows up.
assert_status $LOCKED \
  '[{"name":"HDMI-A-1","solitaryBlockedBy":["WINDOWED","LOCK","CANDIDATE"]}]' \
  "a locked session is detected"

assert_status $LOCKED \
  '[{"name":"eDP-1","solitaryBlockedBy":["WINDOWED"]},{"name":"DP-2","solitaryBlockedBy":["LOCK"]}]' \
  "a lock on any monitor counts as a locked session"

assert_status $UNLOCKED \
  '[{"name":"HDMI-A-1","solitaryBlockedBy":["WINDOWED","CANDIDATE"]}]' \
  "an unlocked session is reported as unlocked"

# A monitor showing a solitary client has no blockers at all.
assert_status $UNLOCKED \
  '[{"name":"HDMI-A-1","solitaryBlockedBy":null}]' \
  "a monitor with no solitary blockers is reported as unlocked"

# LOCK only carries this meaning inside the reason list.
assert_status $UNLOCKED \
  '[{"name":"LOCK-1","description":"LOCK display","activeWorkspace":{"name":"LOCK"},"solitaryBlockedBy":["WINDOWED"]}]' \
  "LOCK elsewhere in the monitor payload is not a locked session"

# Guessing "unlocked" with nothing to read strands the session.
assert_status $UNDETERMINED '[]' \
  "a session with no monitors to read cannot say"

assert_status $UNDETERMINED '[]' \
  "an unreachable compositor cannot say" 1

assert_status $UNDETERMINED 'not json at all' \
  "an unreadable monitor payload cannot say"

# Hyprland stops at the first reason and never reaches the lock check.
assert_status $UNDETERMINED \
  '[{"name":"HDMI-A-1","solitaryBlockedBy":["WORKSPACE"]}]' \
  "a monitor with no workspace yet cannot say"

assert_status $UNLOCKED \
  '[{"name":"HDMI-A-1","solitaryBlockedBy":["WORKSPACE"]},{"name":"DP-2","solitaryBlockedBy":["WINDOWED"]}]' \
  "one readable monitor is enough to answer"

assert_status $LOCKED \
  '[{"name":"HDMI-A-1","solitaryBlockedBy":["WORKSPACE"]},{"name":"DP-2","solitaryBlockedBy":["LOCK"]}]' \
  "a lock is still found alongside a monitor that cannot say"

status=0
timeout --kill-after=1s 4s env AP="$test_ap" ARCH_TEST_HYPRCTL_MODE=slow \
  "$ARCH_TEST_CLI_BIN/arch-hyprland-session-locked" || status=$?
(( status == UNDETERMINED )) || fail "a stalled compositor query is bounded and undetermined" "$status"
pass "a stalled compositor query does not block callers"

sed -i 's/max_output_bytes: 262144/max_output_bytes: 16/' "$test_ap/data/cli/hyprland-session-locked.yml"
status=0
AP="$test_ap" ARCH_TEST_HYPRCTL_MODE=large "$ARCH_TEST_CLI_BIN/arch-hyprland-session-locked" || status=$?
(( status == UNDETERMINED )) || fail "an oversized compositor response is undetermined" "$status"
pass "a compositor response is size bounded before parsing"
