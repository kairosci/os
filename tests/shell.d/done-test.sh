#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

test_home=$(mktemp -d)
trap 'rm -rf "$test_home"' EXIT
export AP="$ROOT"

done_marker="$test_home/.local/state/arch/done/example"

invalid_ap="$test_home/invalid-arch"
mkdir -p "$invalid_ap/data/cli" "$invalid_ap/src"
ln -s "$ROOT/src/arch" "$invalid_ap/src/arch"
printf '[]\n' >"$invalid_ap/data/cli/done.yml"
status=0
output=$(AP="$invalid_ap" HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done check example 2>&1) || status=$?
(( status == 1 )) && [[ $output == *"Could not load done configuration"* ]] ||
  fail "done reports malformed configuration without a traceback" "exit: $status" "$output"
pass "done reports malformed configuration without a traceback"

if HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done check example; then
  fail "done reports an unmarked task as complete"
fi

HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done mark example
[[ -f $done_marker ]] || fail "done marks a task complete"
HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done check example || fail "done reports a marked task as complete"

HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done ensure once || fail "done ensures an unmarked task"
[[ -f $test_home/.local/state/arch/done/once ]] || fail "done ensure marks a task complete"
if HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done ensure once; then
  fail "done ensures a completed task again"
fi

if HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done check ../invalid >/dev/null 2>&1; then
  fail "done accepts marker path traversal"
fi

protected="$test_home/protected"
printf 'protected\n' >"$protected"
ln -s "$protected" "$test_home/.local/state/arch/done/symlink"
if HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done mark symlink >/dev/null 2>&1; then
  fail "done mark refuses a symlink marker"
fi
if HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done ensure symlink >/dev/null 2>&1; then
  fail "done ensure refuses an existing symlink marker"
fi
if HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done check symlink; then
  fail "done check refuses a symlink marker"
fi
[[ -L $test_home/.local/state/arch/done/symlink && $(<"$protected") == protected ]] ||
  fail "done operations do not follow marker symlinks"

mv "$test_home/.local/state/arch/done" "$test_home/.local/state/arch/done.saved"
mkdir "$test_home/outside-done"
ln -s "$test_home/outside-done" "$test_home/.local/state/arch/done"
if HOME="$test_home" "$ARCH_TEST_CLI_BIN/archctl" done mark escaped >/dev/null 2>&1; then
  fail "done refuses a symlinked marker directory"
fi
[[ ! -e $test_home/outside-done/escaped ]] || fail "done does not write outside its marker directory"

pass "done manages completion markers without following symlinks"
