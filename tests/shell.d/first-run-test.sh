#!/bin/bash

source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

mock_bin="$test_tmp/bin"
mkdir -p "$mock_bin" "$test_tmp/home"

cat >"$mock_bin/arch-done" <<'SH'
#!/bin/bash
[[ $1 == check && $2 == first-run-user && ${ARCH_TEST_DONE:-0} == 1 ]]
SH
cat >"$mock_bin/arch-provision-user" <<'SH'
#!/bin/bash
touch "$ARCH_TEST_FINALIZE_CALLED"
SH
chmod +x "$mock_bin/arch-done" "$mock_bin/arch-provision-user"

finalize_called="$test_tmp/finalize-called"
HOME="$test_tmp/home" ARCH_PATH="$ROOT" PATH="$mock_bin:$PATH" \
  ARCH_TEST_DONE=1 ARCH_TEST_FINALIZE_CALLED="$finalize_called" \
  "$ROOT/src/commands/arch-provision-first-run" >"$test_tmp/output"

[[ ! -e $finalize_called ]] || fail "completed first-run exits before setup"
grep -F 'First-run already complete.' "$test_tmp/output" >/dev/null || fail "completed first-run reports its lifecycle gate"

LANG=it_IT.UTF-8 ARCH_PATH="$ROOT" "$ROOT/src/commands/arch-provision-first-run" --help >"$test_tmp/help"
grep -F 'Esegue la configurazione iniziale' "$test_tmp/help" >/dev/null || fail "first-run help uses the Italian YAML strings"

pass "first-run is a Python CLI with a YAML lifecycle gate and localized help"
