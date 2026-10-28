#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

mock_bin="$test_tmp/bin"
test_home="$test_tmp/home"
mise_log="$test_tmp/mise"
mkdir -p "$mock_bin" "$test_home/.local/bin" "$test_home/.cargo/bin"

cat >"$mock_bin/mise" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$ARCH_TEST_MISE_LOG"
SH
chmod +x "$mock_bin/mise"

export HOME="$test_home"
export ARCH_TEST_MISE_LOG="$mise_log"
export PATH="$mock_bin:$ROOT/src/commands:$PATH"

mise_config="$test_tmp/etc/mise/config.toml"
mkdir -p "$(dirname "$mise_config")"
cp "$ROOT/etc/mise/conf.d/arch-tools.toml" "$mise_config"
export ARCH_MISE_CONFIG_PATH="$mise_config"

bash "$ROOT/src/commands/arch-install-dev-env" python >/dev/null
grep -Fx 'use --global python@latest' "$mise_log" >/dev/null || fail "Python setup installs Python through mise"
grep -Fx 'install uv' "$mise_log" >/dev/null || fail "Python setup installs the system-configured uv"
grep -Fx 'use --global uv' "$mise_log" >/dev/null && fail "Python setup leaves the system-configured uv out of the user config"
pass "Python setup installs Python and uv through mise"

# A user can opt out of os's declarations, so uv goes in their own config
# while leaving that opt-out in place.
miserc="$test_home/.config/mise/miserc.toml"
mkdir -p "$(dirname "$miserc")"
printf 'ignored_config_paths = ["%s"]\n' "$mise_config" >"$miserc"
cp "$miserc" "$test_tmp/expected-miserc"
: >"$mise_log"
bash "$ROOT/src/commands/arch-install-dev-env" python >/dev/null
grep -Fx 'use --global uv' "$mise_log" >/dev/null || fail "Python setup selects uv when os's declaration is skipped"
grep -Fx 'install uv' "$mise_log" >/dev/null && fail "Python setup does not count on os's uv when its declaration is skipped"
cmp -s "$miserc" "$test_tmp/expected-miserc" || fail "Python setup keeps the mise opt-out"
rm "$miserc"
pass "Python setup selects uv when os's declaration is skipped"

# Without os's declarations, nothing else declares uv.
rm "$mise_config"
: >"$mise_log"
bash "$ROOT/src/commands/arch-install-dev-env" python >/dev/null
grep -Fx 'use --global uv' "$mise_log" >/dev/null || fail "Python setup selects uv when no system config declares it"
pass "Python setup selects uv without os's declarations"

touch "$test_home/.local/bin/uv" "$test_home/.local/bin/uvx" "$test_home/.cargo/bin/uv"
: >"$mise_log"
bash "$ROOT/src/commands/arch-remove-dev-env" python >/dev/null
grep -Fx 'uninstall python --all' "$mise_log" >/dev/null || fail "Python removal uninstalls mise Python"
grep -Fx 'rm -g python' "$mise_log" >/dev/null || fail "Python removal removes the global Python declaration"
grep -q 'uv' "$mise_log" && fail "Python removal does not remove the independent uv tool"
[[ -e $test_home/.local/bin/uv && -e $test_home/.local/bin/uvx && -e $test_home/.cargo/bin/uv ]] ||
  fail "Python removal preserves uv commands"
pass "Python removal preserves the default uv tool"
