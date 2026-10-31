#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

snapshot="$ROOT/src/arch/cli/snapshot/manage.py"
test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
fake_bin="$test_tmp/bin"
mkdir -p "$fake_bin"

cat >"$fake_bin/archctl" <<'STUB'
#!/bin/bash
case "$*" in
  "cmd missing snapper") exit "${SNAPPER_MISSING:-1}" ;;
  version) [[ ${VERSION_FAILURE:-0} == 0 ]] || exit 1; printf '%s\n' "${SNAPSHOT_VERSION:-4.0.0}" ;;
  *) exit 2 ;;
esac
STUB
cat >"$fake_bin/sudo" <<'STUB'
#!/bin/bash
printf 'sudo %s\n' "$*" >>"$TEST_LOG"
exec "$@"
STUB
cat >"$fake_bin/snapper" <<'STUB'
#!/bin/bash
printf 'snapper %s\n' "$*" >>"$TEST_LOG"
if [[ $* == "--csvout list-configs" ]]; then
  printf 'config,subvolume\n'
  if [[ ${SNAPPER_NO_CONFIGS:-0} == 0 ]]; then
    printf 'root,/\nhome,/home\n'
  fi
fi
STUB
cat >"$fake_bin/limine-snapper-restore" <<'STUB'
#!/bin/bash
printf 'restore %s\n' "$*" >>"$TEST_LOG"
STUB
chmod +x "$fake_bin"/*

run_snapshot() {
  AP="$ROOT" \
  PATH="$fake_bin:$PATH" \
  python3 -I "$snapshot" "$@"
}

: >"$test_tmp/calls.log"
set +e
output=$(TEST_LOG="$test_tmp/calls.log" SNAPPER_MISSING=0 run_snapshot create 2>&1)
status=$?
set -e
(( status == 127 )) || fail "snapshot creation returns 127 when Snapper is absent" "got $status"
[[ -z $output ]] || fail "missing Snapper remains quiet" "$output"
pass "snapshot creation quietly reports missing Snapper with status 127"

: >"$test_tmp/calls.log"
set +e
output=$(TEST_LOG="$test_tmp/calls.log" SNAPPER_NO_CONFIGS=1 run_snapshot create 2>&1)
status=$?
set -e
(( status != 0 )) || fail "snapshot creation fails when Snapper has no configs"
grep -qF 'No Snapper configs found' <<<"$output" ||
  fail "snapshot creation reports that no snapshot was created" "$output"
grep -qF 'sudo snapper -c ' "$test_tmp/calls.log" &&
  fail "snapshot creation does not invent a config to snapshot"
pass "snapshot creation fails loudly when Snapper is installed but unconfigured"

: >"$test_tmp/calls.log"
TEST_LOG="$test_tmp/calls.log" run_snapshot create >"$test_tmp/create.out"
grep -qFx 'snapper -c root create -c number -d 4.0.0' "$test_tmp/calls.log" ||
  fail "snapshot creation snapshots the root config" "$(cat "$test_tmp/calls.log")"
grep -qFx 'snapper -c root cleanup number' "$test_tmp/calls.log" ||
  fail "snapshot creation cleans up the root config"
grep -qFx 'snapper -c home create -c number -d 4.0.0' "$test_tmp/calls.log" ||
  fail "snapshot creation snapshots the home config"
grep -qFx 'snapper -c home cleanup number' "$test_tmp/calls.log" ||
  fail "snapshot creation cleans up the home config"
grep -qF 'Snapshots can be selected during boot.' "$test_tmp/create.out" ||
  fail "snapshot creation reports the boot selection path"
pass "snapshot creation processes every configured Snapper config"

: >"$test_tmp/calls.log"
TEST_LOG="$test_tmp/calls.log" run_snapshot restore
grep -qFx 'restore ' "$test_tmp/calls.log" || fail "restore delegates to the configured snapshot restore command"
pass "snapshot restore delegates to the boot snapshot restore command"

grep -qF 'archctl snapshot create || (($? == 127))' "$ROOT/src/arch/commands/arch-update" ||
  fail "update ignores only the missing-Snapper status"
grep -qF 'archctl snapshot create || (($? == 127))' "$ROOT/src/arch/commands/arch-upgrade-to-quattro" ||
  fail "upgrade ignores only the missing-Snapper status"
pass "update and upgrade continue without Snapper but preserve other snapshot failures"
