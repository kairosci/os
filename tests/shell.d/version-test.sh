#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

stub_bin="$test_tmp/bin"
mkdir -p "$stub_bin" "$test_tmp/checkout/src/arch/cli/version" "$test_tmp/checkout/data/cli"
cp "$ROOT/src/arch/cli/version/info.py" "$test_tmp/checkout/src/arch/cli/version/info.py"
cp "$ROOT/data/cli/version.yml" "$test_tmp/checkout/data/cli/version.yml"

# The edge channel installs arch-dev. Older builds did not declare
# provides=(arch), so a query for plain arch finds nothing there.
cat >"$stub_bin/pacman" <<'STUB'
#!/bin/bash
[[ $1 == "-Q" ]] || exit 1
shift
for package in "$@"; do
  case ",${ARCH_TEST_PACKAGES:-}," in
    *",$package,"*)
      echo "$package ${ARCH_TEST_VERSION:-4.0.0-1}"
      exit 0
      ;;
  esac
done
echo "error: package '$1' was not found" >&2
exit 1
STUB
chmod +x "$stub_bin/pacman"
cat >"$stub_bin/git" <<'STUB'
#!/bin/bash
if [[ $* == *"branch --show-current"* ]]; then
  [[ -n ${ARCH_TEST_BRANCH:-} ]] || exit 1
  printf '%s\n' "$ARCH_TEST_BRANCH"
else
  [[ -n ${ARCH_TEST_HASH:-} ]] || exit 1
  printf '%s\n' "$ARCH_TEST_HASH"
fi
STUB
chmod +x "$stub_bin/git"

version() {
  ARCH_TEST_PACKAGES="$1" \
    AP="${2:-$ROOT}" \
    ARCH_PACKAGED_ROOT="$ROOT" \
    PATH="$stub_bin:$PATH" \
    "$ARCH_TEST_CLI_BIN/archctl" version
}

[[ $(version arch) == "4.0.0-1" ]] || fail "version reports the stable package"
pass "version reports the stable package"

[[ $(version arch-dev) == "4.0.0-1" ]] || fail "version reports the edge package"
pass "version reports the edge package"

# A checkout reports its hash instead, so packages are irrelevant there.
[[ $(version "" "$test_tmp/checkout") == "dev" ]] || fail "version reports a dev checkout"
pass "version reports a dev checkout"

branch=$(AP="$test_tmp/checkout" ARCH_PACKAGED_ROOT="$ROOT" ARCH_TEST_BRANCH="feature/example" \
  PATH="$stub_bin:$PATH" "$ARCH_TEST_CLI_BIN/arch-version-branch")
[[ $branch == "feature/example" ]] || fail "dev branch command reports the active branch" "$branch"
branch=$(AP="$test_tmp/checkout" ARCH_PACKAGED_ROOT="$ROOT" ARCH_TEST_HASH="abc1234" \
  PATH="$stub_bin:$PATH" "$ARCH_TEST_CLI_BIN/arch-version-branch")
[[ $branch == "detached@abc1234" ]] || fail "dev branch command labels a detached checkout" "$branch"
if AP="$ROOT" ARCH_PACKAGED_ROOT="$ROOT" "$ARCH_TEST_CLI_BIN/arch-version-branch"; then
  fail "packaged install has no dev branch"
fi
pass "dev branch reports a branch or detached commit and is empty for a packaged install"

if version "" >/dev/null 2>&1; then
  fail "version fails when no os package is installed"
fi
pass "version fails when no os package is installed"

# The snapshot description is only a label, so a failed lookup must not abort
# the update under set -e.
snapshot_desc=$(
  set -e
  PATH="$stub_bin:$PATH" ARCH_TEST_PACKAGES="" AP=/usr/share/arch \
    bash -c 'DESC="$(archctl version 2>/dev/null || echo unknown)"; echo "$DESC"' 2>/dev/null
) || fail "snapshot survives an unknown version"

[[ $snapshot_desc == "unknown" ]] || fail "snapshot labels an unknown version" "actual: $snapshot_desc"
pass "snapshot survives an unknown version"

cat >"$stub_bin/arch-language" <<'STUB'
#!/bin/bash
printf '%s\n' "${ARCH_TEST_LOCALE:-it_IT.UTF-8}"
STUB
cat >"$stub_bin/date" <<'STUB'
#!/bin/bash
printf '%s\n' "$LC_TIME" >"$ARCH_TEST_DATE_LOCALE"
printf '%s\n' "$@" >"$ARCH_TEST_DATE_ARGS"
printf '%s\n' 'martedì, ottobre 27 2026 alle 19:00'
STUB
chmod +x "$stub_bin/arch-language" "$stub_bin/date"
pacman_log="$test_tmp/pacman.log"
printf '%s\n' \
  '[2026-10-27T18:00:00+0000] [ALPM] upgraded base (1 -> 2)' \
  '[2026-10-27T18:30:00+0000] [ALPM] installed unrelated (1)' \
  '[2026-10-27T19:00:00+0000] [ALPM] upgraded application (3 -> 4)' \
  >"$pacman_log"
ARCH_TEST_DATE_LOCALE="$test_tmp/date-locale" \
  ARCH_TEST_DATE_ARGS="$test_tmp/date-args" \
  ARCH_PACMAN_LOG="$pacman_log" \
  AP="$ROOT" \
  LANG=it_IT.UTF-8 \
  PATH="$stub_bin:$PATH" \
  env -u LC_TIME "$ARCH_TEST_CLI_BIN/arch-version-pkgs" >"$test_tmp/date-output"
[[ $(<"$test_tmp/date-output") == "martedì, ottobre 27 2026 alle 19:00" ]] || fail "package upgrade date is printed by date"
[[ $(<"$test_tmp/date-locale") == "it_IT.UTF-8" ]] || fail "package upgrade date uses the selected locale"
[[ $(<"$test_tmp/date-args") == $'-d\n2026-10-27T19:00:00+0000\n+%A %d %B %Y alle %H:%M' ]] || fail "the last upgraded package timestamp and Italian format reach date" "$(cat "$test_tmp/date-args")"
pass "package upgrade date uses the latest upgrade timestamp and selected display locale"

printf '%s\n' 'commands: [' >"$test_tmp/checkout/data/cli/version.yml"
set +e
version "" "$test_tmp/checkout" >"$test_tmp/invalid-config-output" 2>"$test_tmp/invalid-config-error"
config_status=$?
set -e
[[ $config_status == 78 ]] || fail "version reports invalid configuration at the command boundary" "$config_status"
rg -q "Could not load version configuration" "$test_tmp/invalid-config-error" || fail "version explains invalid configuration"
if rg -q "Traceback" "$test_tmp/invalid-config-error"; then
  fail "version does not leak a traceback for invalid configuration"
fi
pass "version handles malformed YAML at the command boundary"
