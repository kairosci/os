#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

mkdir -p "$tmp_dir/bin" "$tmp_dir/state-home"

cat >"$tmp_dir/bin/powerprofilesctl" <<'EOF'
#!/bin/bash

if [[ $1 == "list" ]]; then
  if [[ ${POWERPROFILES_TEST_MODE:-} == "slow" ]]; then
    exec sleep 10
  elif [[ ${POWERPROFILES_TEST_MODE:-} == "large" ]]; then
    exec head -c 256 /dev/zero
  else
    printf '  power-saver:\n* balanced:\n  performance:\n'
  fi
elif [[ $1 == "set" ]]; then
  [[ ${POWERPROFILES_SET_FAIL:-0} == "0" ]] || exit "$POWERPROFILES_SET_FAIL"
  printf '%s\n' "$2" >>"$POWERPROFILES_LOG"
fi
EOF
chmod +x "$tmp_dir/bin/powerprofilesctl"

cat >"$tmp_dir/bin/busctl" <<'EOF'
#!/bin/bash

if [[ ${ON_BATTERY:-0} == "1" ]]; then
  echo "b true"
else
  echo "b false"
fi
EOF
chmod +x "$tmp_dir/bin/busctl"

cat >"$tmp_dir/bin/arch-shell" <<'EOF'
#!/bin/bash
printf '%s\n' "$*" >>"$POWERPROFILES_REFRESH_LOG"
EOF
chmod +x "$tmp_dir/bin/arch-shell"

export AP="$ROOT"
export PATH="$tmp_dir/bin:$ARCH_TEST_CLI_BIN:$ROOT/src/arch/commands:$PATH"
export POWERPROFILES_LOG="$tmp_dir/calls"
export POWERPROFILES_REFRESH_LOG="$tmp_dir/refresh-calls"
export XDG_STATE_HOME="$tmp_dir/state-home"
profile_state_dir="$XDG_STATE_HOME/arch/powerprofiles"

profiles=$(archctl powerprofiles list)
[[ $profiles == $'performance\nbalanced\npower-saver' ]] || fail "power profile listing keeps the daemon order reversed" "$profiles"
pass "power profile listing prints supported profiles in display order"

active_profiles=$(archctl powerprofiles list --active-state)
[[ $active_profiles == $'performance\t0\nbalanced\t1\npower-saver\t0' ]] || fail "power profile listing reports the active profile" "$active_profiles"
pass "power profile listing reports active state on request"

if archctl powerprofiles list unexpected >/dev/null 2>&1; then
  fail "power profile listing rejects unknown arguments"
fi
pass "power profile listing rejects unknown arguments"

profile_ap="$tmp_dir/profile-ap"
mkdir -p "$profile_ap/data/cli"
ln -s "$ROOT/src" "$profile_ap/src"
ln -s "$ROOT/data/cli/python-entrypoints.yml" "$profile_ap/data/cli/python-entrypoints.yml"
ln -s "$ROOT/data/cli/groups.yml" "$profile_ap/data/cli/groups.yml"
cat >"$profile_ap/data/cli/powerprofiles-list.yml" <<EOF
command: ['$tmp_dir/bin/powerprofilesctl', list]
timeout_seconds: 1
cleanup_timeout_seconds: 1
max_output_bytes: 8
read_chunk_bytes: 4
profile_line_pattern: '^\\s*(?P<active>\\*)?\\s*(?P<name>[a-zA-Z0-9-]+):\\s*$'
active_state_option: --active-state
usage: 'Usage: archctl powerprofiles list [--active-state]'
statuses:
  success: 0
  invalid_arguments: 1
EOF

slow_output=$(timeout --kill-after=1s 4s env AP="$profile_ap" POWERPROFILES_TEST_MODE=slow \
  archctl powerprofiles list) || fail "power profile listing returns when the daemon stalls"
[[ -z $slow_output ]] || fail "a timed out power profile query returns no partial profiles" "$slow_output"
pass "power profile listing bounds a stalled daemon request"

large_output=$(AP="$profile_ap" POWERPROFILES_TEST_MODE=large archctl powerprofiles list) ||
  fail "an oversized power profile response is rejected without failing the caller"
[[ -z $large_output ]] || fail "an oversized power profile response is not retained" "$large_output"
pass "power profile listing caps daemon output before parsing"

"$ARCH_TEST_CLI_BIN/arch-powerprofiles-set" ac balanced
[[ $(<"$profile_state_dir/ac") == "balanced" ]] || fail "power profile stores AC preference"
[[ $(stat -c %a "$profile_state_dir/ac") == "600" ]] || fail "power profile state is private"
[[ $(tail -n 1 "$tmp_dir/calls") == "balanced" ]] || fail "power profile applies selected AC preference"
[[ $(tail -n 1 "$tmp_dir/refresh-calls") == "-q battery refreshPowerProfile" ]] || fail "power profile refreshes the battery indicator after applying"
pass "power profile stores and applies AC preference"

"$ARCH_TEST_CLI_BIN/arch-powerprofiles-set" ac
[[ $(tail -n 1 "$tmp_dir/calls") == "balanced" ]] || fail "power profile restores AC preference"
pass "power profile restores AC preference"

if POWERPROFILES_SET_FAIL=7 "$ARCH_TEST_CLI_BIN/arch-powerprofiles-set" ac performance; then
  fail "power profile reports a failed selection"
else
  failed_status=$?
fi
(( failed_status == 7 )) || fail "power profile preserves the apply command exit status" "$failed_status"
[[ $(<"$profile_state_dir/ac") == "balanced" ]] || fail "power profile preserves preference after failed selection"
pass "power profile persists only successful selections"

"$ARCH_TEST_CLI_BIN/arch-powerprofiles-set" battery performance
[[ $(<"$profile_state_dir/battery") == "performance" ]] || fail "power profile stores battery preference"
pass "power profile stores battery preference separately"

outside_state="$tmp_dir/outside-state"
printf 'preserve this file\n' >"$outside_state"
ln -sf "$outside_state" "$profile_state_dir/battery"
"$ARCH_TEST_CLI_BIN/arch-powerprofiles-set" battery balanced
[[ $(<"$outside_state") == "preserve this file" ]] || fail "power profile state replacement does not follow a symlink"
[[ ! -L $profile_state_dir/battery && $(<"$profile_state_dir/battery") == "balanced" ]] ||
  fail "power profile state replaces a symlink with its own private file"
"$ARCH_TEST_CLI_BIN/arch-powerprofiles-set" battery performance
pass "power profile state writes atomically without following a symlink"

"$ARCH_TEST_CLI_BIN/arch-powerprofiles-set" ac
[[ $(tail -n 1 "$tmp_dir/calls") == "balanced" ]] || fail "battery preference does not replace AC preference"
pass "power profile keeps AC and battery preferences separate"

ON_BATTERY=1 "$ARCH_TEST_CLI_BIN/arch-powerprofiles-set"
[[ $(tail -n 1 "$tmp_dir/calls") == "performance" ]] || fail "autodetect restores battery preference"
pass "power profile autodetect restores battery preference"

rm "$profile_state_dir/ac"
ON_BATTERY=0 "$ARCH_TEST_CLI_BIN/arch-powerprofiles-set"
[[ $(tail -n 1 "$tmp_dir/calls") == "performance" ]] || fail "power profile uses performance as AC default"
pass "power profile retains performance as AC default"

"$ARCH_TEST_CLI_BIN/arch-powerprofiles-set" ac power-saver
"$ROOT/src/arch/commands/arch-powerprofiles-init"
[[ $(tail -n 1 "$tmp_dir/calls") == "power-saver" ]] || fail "init restores the autodetected preference"
pass "power profile init restores the autodetected preference"

rg -F '["arch-powerprofiles-set", pendingPowerSource]' "$ROOT/src/arch/shell/plugins/services/battery/Service.qml" >/dev/null ||
  fail "battery service applies profiles through os command"
pass "battery service applies profiles through os command"

rg -F 'arch-powerprofiles-set autodetect' "$ROOT/src/arch/shell/plugins/menu/Menu.qml" >/dev/null ||
  fail "power profile menu persists selections through os command"
pass "power profile menu persists selections through os command"
