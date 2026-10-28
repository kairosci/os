#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

mock_bin="$test_tmp/bin"
test_home="$test_tmp/home"
mise_config="$test_tmp/etc/mise/config.toml"
mise_log="$test_tmp/mise-log"
mkdir -p "$mock_bin" "$test_home/.config/mise" "$(dirname "$mise_config")"
printf '[tools]\ngh = "latest"\n' >"$mise_config"
cat >"$mock_bin/mise" <<'MOCK'
#!/bin/bash
printf '%s\n' "$*" >>"$ARCH_TEST_MISE_LOG"
MOCK
chmod +x "$mock_bin/mise"
export HOME="$test_home"
export PATH="$mock_bin:$ROOT/src/commands:$PATH"
export ARCH_MISE_CONFIG_PATH="$mise_config"
export ARCH_TEST_MISE_LOG="$mise_log"
miserc="$HOME/.config/mise/miserc.toml"
ignore_line="ignored_config_paths = [\"$mise_config\"]"

printf 'env = ["work"]' >"$miserc"
arch-mise-default-tools disable >/dev/null
arch-mise-default-tools disable >/dev/null
[[ $(<"$miserc") == "env = [\"work\"]"$'\n'"$ignore_line" ]] || fail "opting out adds one setting without replacing the user's config"
grep -Fxq 'reshim' "$mise_log" || fail "opting out retires the lazy shims"
pass "opting out is idempotent and preserves the user's mise settings"

arch-mise-default-tools enable >/dev/null
[[ $(<"$miserc") == 'env = ["work"]' ]] || fail "opting back in removes only os's setting"
grep -Fxq 'reshim --system' "$mise_log" || fail "opting back in rebuilds system shims"
pass "opting back in restores only os's mise setting"

printf 'ignored_config_paths = ["~/old"]\n' >"$miserc"
if arch-mise-default-tools disable >/dev/null 2>&1; then
  fail "opting out refuses to add a duplicate ignored_config_paths setting"
fi
[[ $(<"$miserc") == 'ignored_config_paths = ["~/old"]' ]] || fail "an existing user list remains untouched"
pass "existing mise ignore lists remain under user control"
