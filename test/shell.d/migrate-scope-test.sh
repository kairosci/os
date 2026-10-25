#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

test_root="$test_tmp/arch"
test_home="$test_tmp/home"
mkdir -p "$test_root/migrations" "$test_home"

cat >"$test_root/migrations/100-first.sh" <<'SH'
[[ $ARCH_PATH == "$TEST_EXPECTED_ARCH_PATH" ]]
echo first >>"$TEST_CALLS"
SH
cat >"$test_root/migrations/200-second.sh" <<'SH'
[[ $ARCH_PATH == "$TEST_EXPECTED_ARCH_PATH" ]]
echo second >>"$TEST_CALLS"
SH

calls="$test_tmp/calls"

if ! HOME="$test_home" ARCH_PATH="$test_root" "$ROOT/bin/arch-migrate" --pending >"$test_tmp/pending.out"; then
  fail "migration runner reports pending migrations before state exists"
fi
grep -q '^100-first\.sh$' "$test_tmp/pending.out" || fail "migration runner lists first pending migration filename"
grep -q '^200-second\.sh$' "$test_tmp/pending.out" || fail "migration runner lists second pending migration filename"
pass "migration runner detects pending migrations"

HOME="$test_home" \
ARCH_PATH="$test_root" \
TEST_EXPECTED_ARCH_PATH="$test_root" \
TEST_CALLS="$calls" \
  "$ROOT/bin/arch-migrate" >"$test_tmp/first-run.out"
[[ $(sed -n '1p' "$calls") == "first" ]] || fail "migration runner runs first migration"
[[ $(sed -n '2p' "$calls") == "second" ]] || fail "migration runner runs second migration"
[[ -f $test_home/.local/state/arch/migrations/100-first.sh ]] || fail "migration runner records first migration marker"
[[ -f $test_home/.local/state/arch/migrations/200-second.sh ]] || fail "migration runner records second migration marker"
pass "migration runner runs all migrations"

HOME="$test_home" \
ARCH_PATH="$test_root" \
TEST_EXPECTED_ARCH_PATH="$test_root" \
TEST_CALLS="$calls" \
  "$ROOT/bin/arch-migrate" >"$test_tmp/second-run.out"
[[ $(wc -l <"$calls") -eq 2 ]] || fail "migration runner skips completed migrations"
pass "migration runner skips completed migrations"

if HOME="$test_home" ARCH_PATH="$test_root" "$ROOT/bin/arch-migrate" --pending >"$test_tmp/not-pending.out"; then
  fail "migration runner reports no pending migrations after state exists"
fi
pass "migration runner detects no pending migrations"

deferred_root="$test_tmp/deferred-root"
deferred_home="$test_tmp/deferred-home"
mkdir -p "$deferred_root/migrations" "$deferred_home"
cat >"$deferred_root/migrations/100-deferred.sh" <<'SH'
echo deferred >>"$TEST_CALLS"
[[ ${TEST_DEFERRED:-0} != 1 ]] || exit 75
SH
cat >"$deferred_root/migrations/200-independent.sh" <<'SH'
echo independent >>"$TEST_CALLS"
SH
deferred_calls="$test_tmp/deferred-calls"
HOME="$deferred_home" ARCH_PATH="$deferred_root" \
TEST_CALLS="$deferred_calls" TEST_DEFERRED=1 \
  "$ROOT/bin/arch-migrate" >"$test_tmp/deferred-first.out"
[[ ! -e $deferred_home/.local/state/arch/migrations/100-deferred.sh ]] ||
  fail "a deferred migration is not marked complete"
[[ -f $deferred_home/.local/state/arch/migrations/200-independent.sh ]] ||
  fail "independent migrations run after a deferred migration"
[[ $(tail -n1 "$deferred_calls") == independent ]] ||
  fail "the migration queue continues after a deferred migration"
HOME="$deferred_home" ARCH_PATH="$deferred_root" \
TEST_CALLS="$deferred_calls" TEST_DEFERRED=0 \
  "$ROOT/bin/arch-migrate" >"$test_tmp/deferred-retry.out"
[[ -f $deferred_home/.local/state/arch/migrations/100-deferred.sh ]] ||
  fail "a deferred migration can complete on a later run"
[[ $(wc -l <"$deferred_calls") -eq 3 ]] ||
  fail "the retry reruns only the deferred migration"
pass "deferred migrations do not block independent work and remain retryable"

legacy_home="$test_tmp/legacy-home"
mkdir -p "$legacy_home/.local/state/arch/migrations"
touch "$legacy_home/.local/state/arch/migrations/100-first.sh"
HOME="$legacy_home" ARCH_PATH="$test_root" \
  "$ROOT/bin/arch-migrate" --pending >"$test_tmp/legacy-pending.out"
[[ $(cat "$test_tmp/legacy-pending.out") == "200-second.sh" ]] ||
  fail "migration runner recognizes completion markers in the previous state directory"
pass "migration runner recognizes legacy completion markers"

os_legacy_home="$test_tmp/os-legacy-home"
mkdir -p "$os_legacy_home/.local/state/os/migrations"
touch "$os_legacy_home/.local/state/os/migrations/100-first.sh"
HOME="$os_legacy_home" ARCH_PATH="$test_root" \
  "$ROOT/bin/arch-migrate" --pending >"$test_tmp/os-legacy-pending.out"
[[ $(cat "$test_tmp/os-legacy-pending.out") == "200-second.sh" ]] ||
  fail "migration runner recognizes completion markers in the previous OS state directory"
pass "migration runner recognizes OS-named completion markers"

path_home="$test_tmp/path-home"
mkdir -p "$path_home/config/arch/themes/cosmic" \
  "$path_home/config/arch/extensions" \
  "$path_home/state/arch/current" \
  "$path_home/state/arch/migrations" \
  "$path_home/state/arch/migrations" \
  "$path_home/cache/arch/usage" \
  "$path_home/cache/arch"
printf 'legacy theme\n' >"$path_home/config/arch/themes/cosmic/colors.toml"
printf 'keep this\n' >"$path_home/config/arch/extensions/custom.jsonc"
printf 'cosmic\n' >"$path_home/state/arch/current/theme.name"
touch "$path_home/state/arch/migrations/100-first.sh"
printf 'usage\n' >"$path_home/cache/arch/usage/history.json"
printf 'cache\n' >"$path_home/cache/arch/local.json"
HOME="$path_home" XDG_CONFIG_HOME="$path_home/config" \
XDG_STATE_HOME="$path_home/state" XDG_CACHE_HOME="$path_home/cache" \
  bash "$ROOT/migrations/1792861519.sh"
[[ -f $path_home/config/arch/themes/cosmic/colors.toml &&
  $(cat "$path_home/config/arch/extensions/custom.jsonc") == 'keep this' ]] ||
  fail "home-directory migration merges existing configuration without replacing it"
[[ -f $path_home/state/arch/current/theme.name &&
  -f $path_home/state/arch/migrations/100-first.sh ]] ||
  fail "home-directory migration moves runtime data and keeps completed markers"
[[ -f $path_home/cache/arch/usage/history.json && -f $path_home/cache/arch/local.json ]] ||
  fail "home-directory migration merges cache files"
[[ ! -e $path_home/config/arch && ! -e $path_home/state/arch &&
  ! -e $path_home/cache/arch ]] || fail "home-directory migration removes the old directory names"
[[ ! -e $path_home/config/os && ! -e $path_home/state/os && ! -e $path_home/cache/os ]] ||
  fail "home-directory migration does not recreate intermediate OS directories"
HOME="$path_home" XDG_CONFIG_HOME="$path_home/config" \
XDG_STATE_HOME="$path_home/state" XDG_CACHE_HOME="$path_home/cache" \
  bash "$ROOT/migrations/1792861519.sh"
pass "home-directory migration is idempotent"

conflict_home="$test_tmp/conflict-home"
mkdir -p "$conflict_home/.config/arch" "$conflict_home/.config/arch"
printf 'old\n' >"$conflict_home/.config/arch/settings.json"
printf 'new\n' >"$conflict_home/.config/arch/settings.json"
HOME="$conflict_home" bash "$ROOT/migrations/1792861519.sh" >"$test_tmp/conflict.out" 2>&1
[[ $(cat "$conflict_home/.config/arch/settings.json") == "new" &&
  $(cat "$conflict_home/.config/arch/settings.json.legacy-arch") == "old" &&
  ! -e $conflict_home/.config/arch ]] ||
  fail "home-directory migration preserves conflicting data under the new directory name"
pass "home-directory migration preserves conflicting user data"

arch_home="$test_tmp/arch-home"
mkdir -p "$arch_home/.config/os/extensions" \
  "$arch_home/.local/state/os/current/theme" \
  "$arch_home/.local/state/os/migrations" \
  "$arch_home/.cache/os/usage" \
  "$arch_home/.config/kitty"
printf '{"custom":true}\n' >"$arch_home/.config/os/extensions/custom.jsonc"
printf '{\n  "personal.notes": {"label":"Notes"}\n}\n' >"$arch_home/.config/os/extensions/arch-menu.jsonc"
printf 'cosmic\n' >"$arch_home/.local/state/os/current/theme.name"
touch "$arch_home/.local/state/os/migrations/100-first.sh"
printf 'usage\n' >"$arch_home/.cache/os/usage/history.json"
printf 'include = "~/.local/state/os/current/theme/kitty.conf"\n' >"$arch_home/.config/kitty/kitty.conf"
HOME="$arch_home" bash "$ROOT/migrations/1792865325.sh"
[[ -f $arch_home/.config/arch/extensions/custom.jsonc &&
  -f $arch_home/.config/arch/extensions/arch-menu.jsonc &&
  -f $arch_home/.local/state/arch/current/theme.name &&
  -f $arch_home/.local/state/arch/migrations/100-first.sh &&
  -f $arch_home/.cache/arch/usage/history.json ]] ||
  fail "Arch path migration preserves user settings, theme state, and migration records"
[[ ! -e $arch_home/.config/arch/extensions/arch-menu.jsonc ]] ||
  fail "Arch path migration renames the old user menu extension"
grep -F '.local/state/arch/current/theme/kitty.conf' "$arch_home/.config/kitty/kitty.conf" >/dev/null ||
  fail "Arch path migration updates references in other application configs"
[[ ! -e $arch_home/.config/os && ! -e $arch_home/.local/state/os && ! -e $arch_home/.cache/os ]] ||
  fail "Arch path migration removes the old config, state, and cache directories"
HOME="$arch_home" bash "$ROOT/migrations/1792865325.sh"
pass "home config and state migrate from OS names to Arch idempotently"

failure_root="$test_tmp/failure-arch"
failure_home="$test_tmp/failure-home"
mkdir -p "$failure_root/migrations" "$failure_home"

cat >"$failure_root/migrations/500-fail.sh" <<'SH'
echo before-fail >>"$TEST_CALLS"
false
echo after-fail >>"$TEST_CALLS"
SH

set +e
HOME="$failure_home" \
ARCH_PATH="$failure_root" \
TEST_CALLS="$calls" \
  "$ROOT/bin/arch-migrate" >"$test_tmp/failure.out" 2>"$test_tmp/failure.err"
failure_status=$?
set -e
[[ $failure_status -ne 0 ]] || fail "migration runner exits non-zero when a migration fails"
[[ ! -f $failure_home/.local/state/arch/migrations/500-fail.sh ]] || fail "migration runner does not mark failed migration complete"
grep -q '^before-fail$' "$calls" || fail "migration runner started failing migration"
! grep -q '^after-fail$' "$calls" || fail "migration runner stops failing migration under strict mode"
pass "migration runner does not mark failed migrations complete"

stdin_root="$test_tmp/stdin-arch"
stdin_home="$test_tmp/stdin-home"
stdin_calls="$test_tmp/stdin-calls"
mkdir -p "$stdin_root/migrations" "$stdin_home"

cat >"$stdin_root/migrations/100-reader.sh" <<'SH'
IFS= read -r value
printf 'reader:%s\n' "$value" >>"$TEST_CALLS"
SH
cat >"$stdin_root/migrations/200-after.sh" <<'SH'
echo after-reader >>"$TEST_CALLS"
SH

printf 'migration input\n' | \
  HOME="$stdin_home" \
  ARCH_PATH="$stdin_root" \
  TEST_CALLS="$stdin_calls" \
  "$ROOT/bin/arch-migrate" >"$test_tmp/stdin.out"

grep -q '^reader:migration input$' "$stdin_calls" ||
  fail "migration runner preserves the caller's stdin for a migration" "$(cat "$stdin_calls")"
grep -q '^after-reader$' "$stdin_calls" ||
  fail "a migration reading stdin does not swallow later queue entries" "$(cat "$stdin_calls")"
[[ -f $stdin_home/.local/state/arch/migrations/100-reader.sh &&
  -f $stdin_home/.local/state/arch/migrations/200-after.sh ]] ||
  fail "migration runner marks both stdin-isolated migrations complete"
pass "migration queue uses a private file descriptor instead of migration stdin"
