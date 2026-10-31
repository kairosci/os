#!/bin/bash

set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/base-test.sh"

work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT

fake_home="$work_dir/home"
mkdir -p "$fake_home/.config/arch/hooks" "$fake_home/.local/state/arch"
export AP="$ROOT"

# --- arch-hook --------------------------------------------------------------

# A hook name is a label, not a path. One carrying a slash, or one that is a
# bare `.` or `..`, would run a script from outside the hooks directory.

cat >"$fake_home/.config/arch/hooks/test-hook" <<'SH'
touch "$HOME/hook-ran"
SH

HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook" test-hook
[[ -f $fake_home/hook-ran ]] ||
  fail "archctl hook runs a named hook from the hooks directory"
pass "archctl hook runs a named hook from the hooks directory"

# Dots inside a name are not a path. a..b stays inside the hooks directory.
cat >"$fake_home/.config/arch/hooks/a..b" <<'SH'
touch "$HOME/dotted-hook-ran"
SH

HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook" a..b
[[ -f $fake_home/dotted-hook-ran ]] ||
  fail "archctl hook accepts a hook name with dots in the middle"
pass "archctl hook accepts a hook name with dots in the middle"

cat >"$fake_home/.config/arch/hooks/python-hook.py" <<'PY'
from pathlib import Path
import sys

Path.home().joinpath("python-hook-ran").write_text(" ".join(sys.argv[1:]))
PY
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook" python-hook.py first second
[[ $(<"$fake_home/python-hook-ran") == "first second" ]] || fail "archctl hook runs a Python hook in isolated mode and forwards arguments"
pass "archctl hook runs a Python hook in isolated mode and forwards arguments"

mkdir -p "$fake_home/.config/arch/hooks/hidden-hook.d"
cat >"$fake_home/.config/arch/hooks/hidden-hook.d/.hidden" <<'SH'
touch "$HOME/hidden-hook-ran"
SH
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook" hidden-hook
[[ ! -e $fake_home/hidden-hook-ran ]] || fail "archctl hook ignores hidden files in hook directories"
pass "archctl hook ignores hidden files in hook directories"

for name in . ..; do
  status=0
  HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook" "$name" >/dev/null 2>&1 || status=$?
  (( status == 2 )) ||
    fail "archctl hook refuses a hook name of $name" "exit: $status"
  pass "archctl hook refuses a hook name of $name"
done

# This file sits where a name of ../../evil would resolve: hooks/../.. is
# ~/.config.
cat >"$fake_home/.config/evil" <<'SH'
touch "$HOME/escape-ran"
SH
chmod +x "$fake_home/.config/evil"

status=0
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook" "../../evil" >/dev/null 2>&1 || status=$?
(( status == 2 )) ||
  fail "archctl hook refuses a hook name with a dot-dot" "exit: $status"
[[ ! -e $fake_home/escape-ran ]] ||
  fail "archctl hook runs nothing when it refuses the name"
pass "archctl hook refuses a hook name with a dot-dot"

status=0
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook" "sub/dir" >/dev/null 2>&1 || status=$?
(( status == 2 )) ||
  fail "archctl hook refuses a hook name with a slash" "exit: $status"
pass "archctl hook refuses a hook name with a slash"

# --- arch-hook-install ------------------------------------------------------

# The installer joins the type into ~/.config/arch/hooks/<type>.d before
# mkdir/cp. The runner already refuses a slashed type; install must too, or a
# name the runner will not run still lands on disk.

source_hook="$work_dir/source-hook"
cat >"$source_hook" <<'SH'
#!/bin/bash
true
SH

HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook-install" post-update "$source_hook" >/dev/null
[[ -f $fake_home/.config/arch/hooks/post-update.d/source-hook ]] ||
  fail "archctl hook install still installs a named hook"
pass "archctl hook install still installs a named hook"

HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook-install" a..b "$source_hook" >/dev/null
[[ -f $fake_home/.config/arch/hooks/a..b.d/source-hook ]] ||
  fail "archctl hook install accepts a hook name with dots in the middle"
pass "archctl hook install accepts a hook name with dots in the middle"

for name in . ..; do
  status=0
  HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook-install" "$name" "$source_hook" >/dev/null 2>&1 || status=$?
  (( status == 2 )) ||
    fail "archctl hook install refuses a hook name of $name" "exit: $status"
  [[ ! -e $fake_home/.config/arch/hooks/${name}.d ]] ||
    fail "archctl hook install creates no directory for a hook name of $name"
  pass "archctl hook install refuses a hook name of $name"
done

# hooks/../../evil.d is ~/.config/evil.d. The guard must fire before mkdir.
status=0
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook-install" "../../evil" "$source_hook" >/dev/null 2>&1 || status=$?
(( status == 2 )) ||
  fail "archctl hook install refuses a hook name with a dot-dot" "exit: $status"
[[ ! -e $fake_home/.config/evil.d ]] ||
  fail "archctl hook install creates nothing outside the hooks directory"
pass "archctl hook install refuses a hook name with a dot-dot"

status=0
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-hook-install" "sub/dir" "$source_hook" >/dev/null 2>&1 || status=$?
(( status == 2 )) ||
  fail "archctl hook install refuses a hook name with a slash" "exit: $status"
[[ ! -e $fake_home/.config/arch/hooks/sub ]] ||
  fail "archctl hook install creates no nested directory from a slashed name"
pass "archctl hook install refuses a hook name with a slash"

# Both hook entry points report invalid configuration at their command boundary.
invalid_ap="$work_dir/invalid-hook-arch"
mkdir -p "$invalid_ap/data/cli"
ln -s "$ROOT/src" "$invalid_ap/src"
printf '[]\n' >"$invalid_ap/data/cli/hooks.yml"
for command in arch-hook arch-hook-install; do
  status=0
  output=$(AP="$invalid_ap" HOME="$fake_home" "$ARCH_TEST_CLI_BIN/$command" 2>&1) || status=$?
  (( status == 1 )) && [[ $output == *"Could not load hook configuration"* ]] ||
    fail "$command reports malformed configuration without a traceback" "exit: $status" "$output"
  pass "$command reports malformed configuration without a traceback"
done

# --- arch-state -------------------------------------------------------------

state_dir="$fake_home/.local/state/arch"

invalid_ap="$work_dir/invalid-arch"
mkdir -p "$invalid_ap/data/cli"
mkdir -p "$invalid_ap/src"
ln -s "$ROOT/src/arch" "$invalid_ap/src/arch"
printf '[]\n' >"$invalid_ap/data/cli/state.yml"
status=0
output=$(AP="$invalid_ap" HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-state" set broken 2>&1) || status=$?
(( status == 1 )) && [[ $output == *"Could not load state configuration"* ]] ||
  fail "arch state reports malformed configuration without a traceback" "exit: $status" "$output"
pass "arch state reports malformed configuration without a traceback"

HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-state" set reboot-required
[[ -f $state_dir/reboot-required ]] ||
  fail "arch state set still creates a plain state file"
pass "arch state set still creates a plain state file"

HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-state" set v1..2
[[ -f $state_dir/v1..2 ]] ||
  fail "arch state set accepts a state name with dots in the middle"
pass "arch state set accepts a state name with dots in the middle"

for name in . ..; do
  status=0
  HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-state" set "$name" >/dev/null 2>&1 || status=$?
  (( status == 2 )) ||
    fail "arch state set refuses a state name of $name" "exit: $status"
  pass "arch state set refuses a state name of $name"
done

# state/../.. is ~/.local. The guard must fire before touch gets there.
status=0
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-state" set "../../escape" >/dev/null 2>&1 || status=$?
(( status == 2 )) ||
  fail "arch state set refuses a state name with a dot-dot" "exit: $status"
[[ ! -e $fake_home/.local/escape ]] ||
  fail "arch state set creates nothing outside the state directory"
pass "arch state set refuses a state name with a dot-dot"

status=0
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-state" set "sub/dir" >/dev/null 2>&1 || status=$?
(( status == 2 )) ||
  fail "arch state set refuses a state name with a slash" "exit: $status"
pass "arch state set refuses a state name with a slash"

# clear takes patterns by design ("state-name-or-pattern") and matches
# basenames through find -name, so it can never walk out of the directory.
touch "$state_dir/restart-a-required" "$state_dir/restart-b-required" "$state_dir/keep-me"
printf 'protected\n' >"$fake_home/protected-state-target"
ln -s "$fake_home/protected-state-target" "$state_dir/restart-link-required"
HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-state" clear "restart-*-required"
[[ ! -e $state_dir/restart-a-required && ! -e $state_dir/restart-b-required && -f $state_dir/keep-me ]] ||
  fail "arch state clear still clears matching patterns only"
[[ -L $state_dir/restart-link-required && $(<"$fake_home/protected-state-target") == protected ]] ||
  fail "arch state clear leaves symlinks and their targets untouched"
pass "arch state clear still clears matching patterns only"

if HOME="$fake_home" "$ARCH_TEST_CLI_BIN/arch-state" set restart-link-required >/dev/null 2>&1; then
  fail "arch state set refuses a symlink marker"
fi
[[ -L $state_dir/restart-link-required && $(<"$fake_home/protected-state-target") == protected ]] ||
  fail "arch state set does not follow a marker symlink"
pass "arch state set refuses to follow marker symlinks"
