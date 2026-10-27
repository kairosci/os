#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

unset MISE_DATA_DIR XDG_DATA_HOME

run_bootstrap() {
  local shell_bin="$1"
  local bootstrap="$2"
  local home="$3"
  local path_value="$4"

  shell_bin=$(command -v "$shell_bin")
  HOME="$home" PATH="$path_value" "$shell_bin" -c '
    . "$1"
    printf "%s\n%s\n" "$ARCH_PATH" "$PATH"
  ' sh "$bootstrap"
}

assert_path_present() {
  local path_value="$1"
  local entry="$2"
  local description="$3"

  case ":$path_value:" in
    *":$entry:"*) pass "$description" ;;
    *) fail "$description" "PATH does not contain $entry in $path_value" ;;
  esac
}

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

home="$tmpdir/home"
mkdir -p "$tmpdir/active/src/cli" "$tmpdir/unrelated/bin"

# Test against a copy so the test controls /etc/arch.conf without mutating the host.
bootstrap="$tmpdir/env-bootstrap"
sed "s#/etc/arch.conf#$tmpdir/arch.conf#g" "$ROOT/default/bash/env-bootstrap" >"$bootstrap"

printf 'export ARCH_PATH="/usr/share/arch"\n' >"$tmpdir/arch.conf"
mapfile -t default_result < <(run_bootstrap bash "$bootstrap" "$home" "$tmpdir/unrelated/bin:/usr/bin")
default_path=${default_result[1]}

[[ ${default_result[0]} == /usr/share/arch ]] || fail "env-bootstrap resolves default ARCH_PATH" "actual: ${default_result[0]}"
pass "env-bootstrap resolves default ARCH_PATH"
assert_path_present "$default_path" "$tmpdir/unrelated/bin" "env-bootstrap preserves PATH entries in default mode"
assert_path_present "$default_path" "$home/.local/share/mise/shims" "env-bootstrap appends mise shims"
assert_path_present "$default_path" "$home/.local/bin" "env-bootstrap appends ~/.local/bin"
[[ $default_path != *"command-wrappers/bin"* ]] || fail "env-bootstrap does not add agent wrapper paths" "$default_path"
pass "env-bootstrap does not add agent wrapper paths"

printf 'export ARCH_PATH="%s"\n' "$tmpdir/active" >"$tmpdir/arch.conf"
mapfile -t linked_result < <(run_bootstrap bash "$bootstrap" "$home" "$tmpdir/unrelated/bin:/usr/bin")
linked_path=${linked_result[1]}

[[ ${linked_result[0]} == "$tmpdir/active" ]] || fail "env-bootstrap resolves linked ARCH_PATH" "actual: ${linked_result[0]}"
pass "env-bootstrap resolves linked ARCH_PATH"
[[ $linked_path != *"command-wrappers/bin"* ]] || fail "env-bootstrap keeps agent wrapper paths out of linked mode" "$linked_path"
assert_path_present "$linked_path" "$tmpdir/active/src/cli" "env-bootstrap includes the active checkout CLI in linked mode"
assert_path_present "$linked_path" "$tmpdir/unrelated/bin" "env-bootstrap preserves unrelated PATH entries in linked mode"

mapfile -t linked_duplicate_result < <(run_bootstrap bash "$bootstrap" "$home" "$tmpdir/active/src/cli:/usr/bin:$home/.local/share/mise/shims:$home/.local/bin")
linked_duplicate_path=${linked_duplicate_result[1]}
[[ $linked_duplicate_path == "$tmpdir/active/src/cli:/usr/bin:$home/.local/share/mise/shims:$home/.local/bin" ]] || fail "env-bootstrap does not duplicate PATH entries" "actual PATH: $linked_duplicate_path"
pass "env-bootstrap does not duplicate PATH entries"

# An empty PATH must not produce empty entries (a bare ":" means the cwd)
mapfile -t empty_path_result < <(run_bootstrap bash "$bootstrap" "$home" "")
empty_path=${empty_path_result[1]}
[[ $empty_path == "$tmpdir/active/src/cli:$home/.local/share/mise/shims:$home/.local/bin" ]] || fail "env-bootstrap builds a clean PATH from an empty one" "actual PATH: $empty_path"
pass "env-bootstrap builds a clean PATH from an empty one"

if command -v zsh >/dev/null 2>&1; then
  mapfile -t zsh_result < <(run_bootstrap zsh "$bootstrap" "$home" "$tmpdir/unrelated/bin:/usr/bin")
  zsh_path=${zsh_result[1]}
  [[ $zsh_path != *"command-wrappers/bin"* ]] || fail "env-bootstrap works when sourced by zsh" "$zsh_path"
  assert_path_present "$zsh_path" "$tmpdir/unrelated/bin" "env-bootstrap zsh mode preserves unrelated PATH entries"
fi

mapfile -t repeated_result < <(run_bootstrap bash "$bootstrap" "$home" "$linked_duplicate_path")
[[ ${repeated_result[1]} == "$linked_duplicate_path" ]] || fail "repeated bootstrap leaves PATH unchanged"
pass "repeated bootstrap leaves PATH unchanged"

mapfile -t custom_data_result < <(MISE_DATA_DIR="$tmpdir/custom-mise" run_bootstrap bash "$bootstrap" "$home" "/usr/bin")
[[ ${custom_data_result[1]} != *"command-wrappers/bin"* ]] || fail "env-bootstrap does not add agent wrapper paths for a custom mise data directory"
