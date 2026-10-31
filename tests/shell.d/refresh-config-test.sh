#!/bin/bash

source "$(dirname "${BASH_SOURCE[0]}")/base-test.sh"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

home="$tmpdir/home"
ap="$tmpdir/arch"

mkdir -p "$home/.config/hypr" "$home/.config/arch" "$ap/config/hypr" \
  "$home/.config/tmux" "$ap/config/tmux" "$ap/data/cli" "$ap/scripts" \
  "$ap/src/arch/commands" "$ap/src/arch/python" "$ap/default"
printf 'en\n' >"$home/.config/arch/language"
ln -s "$ROOT/data/cli/refresh-config.yml" "$ap/data/cli/refresh-config.yml"
ln -s "$ROOT/data/cli/refresh-actions.yml" "$ap/data/cli/refresh-actions.yml"
ln -s "$ROOT/scripts/cli_entrypoints.py" "$ap/scripts/cli_entrypoints.py"
ln -s "$ROOT/src/arch/commands/arch-i18n" "$ap/src/arch/commands/arch-i18n"
ln -s "$ROOT/src/arch/cli" "$ap/src/arch/cli"
ln -s "$ROOT/default/i18n" "$ap/default/i18n"
printf 'set -g mouse on\n' >"$ap/config/tmux/tmux.conf"

restart_bin="$tmpdir/bin"
mkdir -p "$restart_bin"
cat >"$restart_bin/arch-restart-tmux" <<'EOF'
#!/bin/bash
printf restarted >"$MARKER"
EOF
chmod +x "$restart_bin/arch-restart-tmux"

cat >"$ap/config/hypr/bindings.lua" <<'EOF'
-- refreshed from AP
EOF

cat >"$home/.config/hypr/bindings.lua" <<'EOF'
-- existing user config
EOF

HOME="$home" AP="$ap" "$ARCH_TEST_CLI_BIN/archctl" refresh config hypr/bindings.lua >/dev/null

cmp -s "$ap/config/hypr/bindings.lua" "$home/.config/hypr/bindings.lua" ||
  fail "refresh-config copies from AP/config"

backup=$(find "$home/.config/hypr" -name 'bindings.lua.bak.*' -print -quit)
[[ -n $backup ]] || fail "refresh-config backs up replaced user config"
grep -Fq -- '-- existing user config' "$backup" ||
  fail "refresh-config backup contains previous user config"

[[ $(stat -c '%a' "$home/.config/hypr/bindings.lua") == "644" ]] ||
  fail "refresh-config preserves the replaced file's permissions"
[[ $(stat -c '%a' "$backup") == "600" ]] || fail "refresh-config stores backups privately"
pass "refresh-config copies from AP/config and backs up existing files privately"

if HOME="$home" AP="$ap" "$ARCH_TEST_CLI_BIN/archctl" refresh config ../escape.lua >"$tmpdir/out" 2>"$tmpdir/err"; then
  fail "refresh-config rejects traversal components"
fi
[[ $(<"$tmpdir/err") == "Use a plain relative configuration file path: ../escape.lua" ]] ||
  fail "refresh-config explains traversal rejection"
pass "refresh-config rejects traversal components"

printf 'source outside boundary\n' >"$tmpdir/outside-source.lua"
ln -s "$tmpdir/outside-source.lua" "$ap/config/hypr/escape.lua"
if HOME="$home" AP="$ap" "$ARCH_TEST_CLI_BIN/archctl" refresh config hypr/escape.lua >"$tmpdir/out" 2>"$tmpdir/err"; then
  fail "refresh-config rejects a shipped-config symlink that escapes its tree"
fi
[[ $(<"$tmpdir/outside-source.lua") == "source outside boundary" ]] ||
  fail "source symlink rejection leaves its target unchanged"
pass "refresh-config rejects source symlinks outside the shipped config tree"

printf 'replacement\n' >"$ap/config/hypr/escape-destination.lua"
printf 'protected\n' >"$tmpdir/outside-destination.lua"
ln -s "$tmpdir/outside-destination.lua" "$home/.config/hypr/escape-destination.lua"
if HOME="$home" AP="$ap" "$ARCH_TEST_CLI_BIN/archctl" refresh config hypr/escape-destination.lua >"$tmpdir/out" 2>"$tmpdir/err"; then
  fail "refresh-config rejects a destination symlink that escapes its tree"
fi
[[ $(<"$tmpdir/outside-destination.lua") == "protected" ]] ||
  fail "destination symlink rejection leaves its target unchanged"
pass "refresh-config rejects destination symlinks outside the user config tree"

mkdir "$tmpdir/outside-config-dir"
printf 'protected parent target\n' >"$tmpdir/outside-config-dir/payload.lua"
mkdir "$ap/config/hypr/escaped-parent"
printf 'parent replacement\n' >"$ap/config/hypr/escaped-parent/payload.lua"
ln -s "$tmpdir/outside-config-dir" "$home/.config/hypr/escaped-parent"
if HOME="$home" AP="$ap" "$ARCH_TEST_CLI_BIN/archctl" refresh config hypr/escaped-parent/payload.lua >"$tmpdir/out" 2>"$tmpdir/err"; then
  fail "refresh-config rejects a destination parent symlink that escapes its tree"
fi
[[ $(<"$tmpdir/outside-config-dir/payload.lua") == "protected parent target" ]] ||
  fail "destination parent symlink rejection leaves its target unchanged"
pass "refresh-config rejects destination parent symlinks outside the user config tree"

printf 'internal replacement\n' >"$ap/config/hypr/pointer.lua"
printf 'internal target\n' >"$home/.config/hypr/pointer-target.lua"
chmod 600 "$home/.config/hypr/pointer-target.lua"
ln -s pointer-target.lua "$home/.config/hypr/pointer.lua"
HOME="$home" AP="$ap" "$ARCH_TEST_CLI_BIN/archctl" refresh config hypr/pointer.lua >/dev/null
[[ -L $home/.config/hypr/pointer.lua ]] || fail "refresh-config preserves an in-tree destination symlink"
[[ $(<"$home/.config/hypr/pointer-target.lua") == "internal replacement" ]] ||
  fail "refresh-config replaces the target of an in-tree symlink"
[[ $(stat -c '%a' "$home/.config/hypr/pointer-target.lua") == "600" ]] ||
  fail "refresh-config preserves target permissions through an in-tree symlink"
pass "refresh-config preserves an in-tree destination symlink and target permissions"

invalid_ap="$tmpdir/invalid-arch"
mkdir -p "$invalid_ap/data/cli" "$invalid_ap/src"
ln -s "$ROOT/src/arch" "$invalid_ap/src/arch"
printf '[]\n' >"$invalid_ap/data/cli/refresh-config.yml"
status=0
output=$(HOME="$home" AP="$invalid_ap" \
  "$ARCH_TEST_CLI_BIN/archctl" refresh config hypr/bindings.lua 2>&1) || status=$?
(( status == 1 )) && [[ $output == *"Could not load refresh configuration"* ]] ||
  fail "refresh-config reports malformed configuration without a traceback" "exit: $status" "$output"
pass "refresh-config reports malformed configuration without a traceback"

if HOME="$home" AP="$ap" "$ARCH_TEST_CLI_BIN/archctl" refresh config hypr/missing.lua >"$tmpdir/out" 2>"$tmpdir/err"; then
  fail "refresh-config rejects configs missing from AP/config"
fi

grep -Fq 'Not a shipped user config: hypr/missing.lua' "$tmpdir/err" ||
  fail "refresh-config reports missing shipped config"

pass "refresh-config validates against AP/config"

marker="$tmpdir/tmux-restarted"
HOME="$home" AP="$ap" MARKER="$marker" PATH="$restart_bin:$PATH" \
  "$ARCH_TEST_CLI_BIN/archctl" refresh tmux
[[ $(<"$home/.config/tmux/tmux.conf") == 'set -g mouse on' ]] ||
  fail "refresh tmux restores the shipped tmux config"
[[ $(<"$marker") == restarted ]] || fail "refresh tmux restarts tmux after restoring its config"
pass "refresh tmux restores its config and restarts tmux"

printf 'decoration = "shader"\n' >"$ap/config/hypr/hyprsunset.conf"
hyprsunset_marker="$tmpdir/hyprsunset-restarted"
hyprsunset_bin="$tmpdir/hyprsunset-bin"
mkdir -p "$hyprsunset_bin"
cat >"$hyprsunset_bin/archctl" <<'EOF'
#!/bin/bash
if [[ $* == "restart app hyprsunset" ]]; then
  printf restarted >"$MARKER"
else
  exec "$ARCH_TEST_CLI_BIN/archctl" "$@"
fi
EOF
chmod +x "$hyprsunset_bin/archctl"
HOME="$home" AP="$ap" MARKER="$hyprsunset_marker" PATH="$hyprsunset_bin:$PATH" \
  "$ARCH_TEST_CLI_BIN/archctl" refresh hyprsunset
[[ $(<"$home/.config/hypr/hyprsunset.conf") == 'decoration = "shader"' ]] ||
  fail "refresh hyprsunset restores the shipped config"
[[ $(<"$hyprsunset_marker") == restarted ]] || fail "refresh hyprsunset restarts its service after restoring config"
pass "refresh hyprsunset restores its config and restarts its service"
