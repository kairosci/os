#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

stub_bin="$test_tmp/bin"
calls="$test_tmp/calls"
mkdir -p "$stub_bin"

cat >"$stub_bin/arch-update-available" <<'SH'
#!/bin/bash

printf 'available\n' >>"$CALLS"
SH

cat >"$stub_bin/arch-shell" <<'SH'
#!/bin/bash

printf 'shell %s\n' "$*" >>"$CALLS"
SH

chmod +x "$stub_bin/arch-update-available" "$stub_bin/arch-shell"

# An older arch-update, already parsed when the upgrade replaced it, still
# calls this once the packages are in.
PATH="$stub_bin:$PATH" CALLS="$calls" "$ROOT/src/cli/arch-update-status"
[[ $(<"$calls") == "shell -q arch.system-update clear" ]] ||
  fail "update status clears the shell indicator without rechecking" "$(<"$calls")"
pass "update status clears the shell indicator without rechecking"
