#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

export AP="$ROOT"

if AP="$ROOT" "$ROOT/src/arch/commands/archctl" cmd present -p; then
  fail "cmd-present treats an option-shaped command name literally"
fi
pass "cmd-present treats an option-shaped command name literally"

AP="$ROOT" "$ROOT/src/arch/commands/archctl" cmd missing -p ||
  fail "cmd-missing treats an option-shaped command name literally"
pass "cmd-missing treats an option-shaped command name literally"

AP="$ROOT" "$ROOT/src/arch/commands/archctl" cmd present bash || fail "cmd-present still finds an ordinary command"
pass "cmd-present still finds an ordinary command"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

mock_bin="$test_tmp/bin"
mkdir -p "$mock_bin"

cat >"$mock_bin/pacman" <<'STUB'
#!/bin/bash

if [[ -n ${ARCH_TEST_PACKAGE_CALLS:-} ]]; then
  {
    printf 'pacman'
    printf ' <%s>' "$@"
    printf '\n'
  } >>"$ARCH_TEST_PACKAGE_CALLS"
fi

if [[ $1 == "-S" ]]; then
  exit 0
elif [[ $1 != "-Q" ]]; then
  exit 2
fi
shift

if [[ ${1:-} == "--" ]]; then
  shift
fi

if [[ ${1:-} == "stalled" ]]; then
  sleep 6
fi

if [[ -n ${ARCH_TEST_PACKAGE_CALLS:-} ]]; then
  exit 0
elif [[ ${1:-} == "--" ]]; then
  shift
  [[ ${1:-} == "installed" ]]
else
  [[ ${1:-} == "installed" ]]
fi
STUB
chmod +x "$mock_bin/pacman"

if AP="$ROOT" PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/archctl" pkg present -- --help; then
  fail "pkg-present treats an option-shaped package name literally"
fi
pass "pkg-present treats an option-shaped package name literally"

AP="$ROOT" PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/archctl" pkg missing -- --help ||
  fail "pkg-missing treats an option-shaped package name literally"
pass "pkg-missing treats an option-shaped package name literally"

AP="$ROOT" PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/archctl" pkg present installed ||
  fail "pkg-present still finds an installed package"
pass "pkg-present still finds an installed package"

timeout_output="$test_tmp/pkg-timeout-output"
timeout_status=0
AP="$ROOT" PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/archctl" pkg present stalled \
  >/dev/null 2>"$timeout_output" || timeout_status=$?
(( timeout_status == 2 )) || fail "pkg-present times out a stalled package query" "status=$timeout_status"
grep -F "Could not check installed packages" "$timeout_output" >/dev/null ||
  fail "pkg-present explains a stalled package query" "$(<"$timeout_output")"
pass "pkg-present bounds a stalled package query"

package_calls="$test_tmp/package-calls"
cat >"$mock_bin/archctl" <<'STUB'
#!/bin/bash
[[ $1 == pkg && $2 == missing ]]
exit 0
STUB
cat >"$mock_bin/sudo" <<'STUB'
#!/bin/bash

exec "$@"
STUB
cat >"$mock_bin/yay" <<'STUB'
#!/bin/bash

: "${ARCH_TEST_PACKAGE_CALLS:?}"
{
  printf 'yay'
  printf ' <%s>' "$@"
  printf '\n'
} >>"$ARCH_TEST_PACKAGE_CALLS"
STUB
chmod +x "$mock_bin/archctl" "$mock_bin/sudo" "$mock_bin/yay"

: >"$package_calls"
PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_PACKAGE_CALLS="$package_calls" \
  "$ROOT/src/arch/commands/arch-pkg-add" --hookdir=/tmp/hooks

grep -Fx 'pacman <-S> <--noconfirm> <--needed> <--> <--hookdir=/tmp/hooks>' "$package_calls" >/dev/null ||
  fail "pkg-add separates package operands from pacman options" "$(<"$package_calls")"
grep -Fx 'pacman <-Q> <--> <--hookdir=/tmp/hooks>' "$package_calls" >/dev/null ||
  fail "pkg-add verifies an option-shaped package name literally" "$(<"$package_calls")"
pass "pkg-add keeps option-shaped package names out of pacman option parsing"

: >"$package_calls"
PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_PACKAGE_CALLS="$package_calls" \
  "$ROOT/src/arch/commands/arch-pkg-aur-add" --hookdir=/tmp/hooks

grep -Fx 'yay <-S> <--noconfirm> <--needed> <--> <--hookdir=/tmp/hooks>' "$package_calls" >/dev/null ||
  fail "pkg-aur-add separates package operands from yay options" "$(<"$package_calls")"
grep -Fx 'pacman <-Q> <--> <--hookdir=/tmp/hooks>' "$package_calls" >/dev/null ||
  fail "pkg-aur-add verifies an option-shaped package name literally" "$(<"$package_calls")"
pass "pkg-aur-add keeps option-shaped package names out of package-manager option parsing"

cat >"$mock_bin/grep" <<'STUB'
#!/bin/bash

if [[ $1 != "-qi" ]]; then
  exit 2
fi
shift

if [[ ${1:-} == "--help" ]]; then
  exit 0
elif [[ ${1:-} == "--" ]]; then
  shift
fi
[[ ${1:-} == "known-hardware" ]]
STUB
chmod +x "$mock_bin/grep"

if AP="$ROOT" PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/archctl" hw match -- --help; then
  fail "hw-match treats an option-shaped hardware pattern literally"
fi
pass "hw-match treats an option-shaped hardware pattern literally"

AP="$ROOT" PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/archctl" hw match known-hardware ||
  fail "hw-match still accepts an ordinary hardware pattern"
pass "hw-match still accepts an ordinary hardware pattern"

pkill_calls="$test_tmp/pkill-calls"
setsid_calls="$test_tmp/setsid-calls"
cat >"$mock_bin/pkill" <<'STUB'
#!/bin/bash

: "${ARCH_TEST_PKILL_CALLS:?}"
printf '<%s>\n' "$@" >"$ARCH_TEST_PKILL_CALLS"
exit "${ARCH_TEST_PKILL_STATUS:-0}"
STUB
cat >"$mock_bin/setsid" <<'STUB'
#!/bin/bash

if [[ -n ${ARCH_TEST_SETSID_CALLS:-} ]]; then
  printf '<%s>\n' "$@" >"$ARCH_TEST_SETSID_CALLS"
fi
exit 0
STUB
chmod +x "$mock_bin/pkill" "$mock_bin/setsid"

PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_PKILL_CALLS="$pkill_calls" \
  ARCH_TEST_SETSID_CALLS="$setsid_calls" "$ROOT/src/arch/commands/archctl" restart app "-9 kitty"

pkill_argv=$(<"$pkill_calls")
[[ $pkill_argv == $'<-x>\n<-->\n<-9 kitty>' ]] ||
  fail "restart-app treats the application name as one literal pkill pattern" "$pkill_argv"
pass "restart-app treats the application name as one literal pkill pattern"
[[ $(<"$setsid_calls") == $'<uwsm-app>\n<-->\n<-9 kitty>' ]] ||
  fail "restart-app preserves application arguments without shell evaluation" "$(<"$setsid_calls")"
pass "restart-app preserves application arguments without shell evaluation"
: >"$pkill_calls"
: >"$setsid_calls"
PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_PKILL_CALLS="$pkill_calls" \
  ARCH_TEST_SETSID_CALLS="$setsid_calls" "$ROOT/src/arch/commands/archctl" restart app \
  >"$test_tmp/restart-app-usage" 2>&1
[[ ! -s $pkill_calls && ! -s $setsid_calls ]] ||
  fail "restart-app validates arguments before stopping or launching processes"
grep -F "Usage:" "$test_tmp/restart-app-usage" >/dev/null ||
  fail "restart-app shows usage when the application name is missing"
pass "restart-app validates arguments before stopping or launching processes"
: >"$pkill_calls"
: >"$setsid_calls"
PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_PKILL_CALLS="$pkill_calls" \
  ARCH_TEST_SETSID_CALLS="$setsid_calls" "$ROOT/src/arch/commands/archctl" restart hyprsunset
[[ $(<"$pkill_calls") == $'<-x>\n<-->\n<hyprsunset>' && \
  $(<"$setsid_calls") == $'<uwsm-app>\n<-->\n<hyprsunset>' ]] ||
  fail "the hidden hyprsunset compatibility entrypoint uses the shared restart module"
pass "the hidden hyprsunset compatibility entrypoint uses the shared restart module"

PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_PKILL_CALLS="$pkill_calls" \
  ARCH_TEST_PKILL_STATUS=1 "$ROOT/src/arch/commands/archctl" restart btop
[[ $(<"$pkill_calls") == $'<-SIGUSR2>\n<-x>\n<btop>' ]] ||
  fail "restart btop signals only btop and treats an absent process as a no-op" "$(<"$pkill_calls")"
pass "restart btop preserves its signal and missing-process behavior"

cat >"$mock_bin/pgrep" <<'STUB'
#!/bin/bash
printf '<%s>\n' "$@" >"$ARCH_TEST_PGREP_CALLS"
exit "${ARCH_TEST_PGREP_STATUS:-0}"
STUB
cat >"$mock_bin/tmux" <<'STUB'
#!/bin/bash
printf '<%s>\n' "$@" >>"$ARCH_TEST_TMUX_CALLS"
if [[ ${1:-} == "has-session" ]]; then
  exit "${ARCH_TEST_TMUX_SESSION_STATUS:-0}"
fi
STUB
chmod +x "$mock_bin/pgrep" "$mock_bin/tmux"

pgrep_calls="$test_tmp/pgrep-calls"
: >"$pkill_calls"
PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_PGREP_CALLS="$pgrep_calls" \
  ARCH_TEST_PGREP_STATUS=1 ARCH_TEST_PKILL_CALLS="$pkill_calls" \
  "$ROOT/src/arch/commands/archctl" restart helix
[[ $(<"$pgrep_calls") == $'<-x>\n<helix>' && ! -s $pkill_calls ]] ||
  fail "restart helix leaves a missing editor alone"
pass "restart helix skips a process that is not running"

PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_PGREP_CALLS="$pgrep_calls" \
  ARCH_TEST_PGREP_STATUS=0 ARCH_TEST_PKILL_CALLS="$pkill_calls" \
  "$ROOT/src/arch/commands/archctl" restart helix
[[ $(<"$pkill_calls") == $'<-USR1>\n<helix>' ]] ||
  fail "restart helix signals a running editor with the configured signal"
pass "restart helix reloads a running editor"

tmux_calls="$test_tmp/tmux-calls"
tmux_config_home="$test_tmp/tmux-config"
mkdir -p "$tmux_config_home/tmux"
PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" XDG_CONFIG_HOME="$tmux_config_home" \
  ARCH_TEST_TMUX_CALLS="$tmux_calls" "$ROOT/src/arch/commands/archctl" restart tmux
[[ $(<"$tmux_calls") == $'<has-session>\n<source-file>\n<'"$tmux_config_home"'/tmux/tmux.conf>' ]] ||
  fail "restart tmux reloads the config from XDG_CONFIG_HOME" "$(<"$tmux_calls")"
pass "restart tmux reloads the configured tmux file"

fake_home="$test_tmp/home"
editor_calls="$test_tmp/editor-calls"
mkdir -p "$fake_home/.local/state/arch/defaults"
printf 'nvim\n' >"$fake_home/.local/state/arch/defaults/editor"

cat >"$mock_bin/nvim" <<'STUB'
#!/bin/bash

: "${ARCH_TEST_EDITOR_CALLS:?}"
printf '<%s>\n' "$@" >"$ARCH_TEST_EDITOR_CALLS"
STUB
chmod +x "$mock_bin/nvim"

HOME="$fake_home" PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_EDITOR_CALLS="$editor_calls" \
  "$ROOT/src/arch/commands/arch-launch-editor" --inline -cquit

editor_argv=$(<"$editor_calls")
[[ $editor_argv == $'<-->\n<-cquit>' ]] ||
  fail "launch-editor separates an option-shaped path from editor options" "$editor_argv"
pass "launch-editor separates an option-shaped path from editor options"

cat >"$mock_bin/archctl" <<'STUB'
#!/bin/bash

if [[ ${1:-} != "launch" || ${2:-} != "tui" ]]; then
  exec "$ROOT/src/arch/commands/archctl" "$@"
fi
: "${ARCH_TEST_EDITOR_CALLS:?}"
printf '<%s>\n' "$@" >"$ARCH_TEST_EDITOR_CALLS"
STUB
chmod +x "$mock_bin/archctl"

HOME="$fake_home" PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_EDITOR_CALLS="$editor_calls" \
  "$ROOT/src/arch/commands/arch-launch-editor" -cquit

editor_argv=$(<"$editor_calls")
[[ $editor_argv == $'<launch>\n<tui>\n<nvim>\n<-->\n<-cquit>' ]] ||
  fail "launch-editor separates a terminal editor path from editor options" "$editor_argv"
pass "launch-editor separates a terminal editor path from editor options"

: >"$setsid_calls"
AP="$ROOT" PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_SETSID_CALLS="$setsid_calls" \
  "$ROOT/src/arch/commands/archctl" launch tui nvim -- -cquit
[[ $(<"$setsid_calls") == $'<uwsm-app>\n<-->\n<xdg-terminal-exec>\n<--app-id=org.arch.nvim>\n<-e>\n<nvim>\n<-->\n<-cquit>' ]] ||
  fail "launch-tui passes the app ID and command arguments as separate argv entries" "$(<"$setsid_calls")"
pass "launch-tui passes the app ID and command arguments as separate argv entries"

: >"$setsid_calls"
hypr_calls="$test_tmp/hypr-calls"
cat >"$mock_bin/hyprctl" <<'STUB'
#!/bin/bash

if [[ $1 == "clients" ]]; then
  if [[ -n ${ARCH_TEST_HYPR_CLIENTS_DELAY:-} ]]; then
    exec sleep "$ARCH_TEST_HYPR_CLIENTS_DELAY"
  fi
  printf '%s\n' "${ARCH_TEST_HYPR_CLIENTS_JSON:?}"
  exit 0
fi
if [[ $1 == "dispatch" ]]; then
  printf '<%s>\n' "$@" >>"${ARCH_TEST_HYPR_CALLS:?}"
  exit "${ARCH_TEST_HYPR_FOCUS_STATUS:-0}"
fi
exit 2
STUB
chmod +x "$mock_bin/hyprctl"
printf '%s\n' '[{"class":"org.arch.editor","title":"Editor","address":"0x123"}]' >"$test_tmp/hypr-clients"
: >"$hypr_calls"
AP="$ROOT" PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_HYPR_CALLS="$hypr_calls" \
  ARCH_TEST_HYPR_CLIENTS_JSON="$(<"$test_tmp/hypr-clients")" \
  "$ROOT/src/arch/commands/archctl" launch tui focus --app-id=org.arch.editor nvim
[[ $(<"$hypr_calls") == $'<dispatch>\n<hl.dsp.focus({ window = "address:0x123" })>' && ! -s $setsid_calls ]] ||
  fail "launch-tui focus selects a matching window without launching a second terminal" "$(<"$hypr_calls")"
pass "launch-tui focus selects a matching window without launching a second terminal"

: >"$setsid_calls"
focus_started=$SECONDS
AP="$ROOT" PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_SETSID_CALLS="$setsid_calls" \
  ARCH_TEST_HYPR_CLIENTS_DELAY=6 \
  "$ROOT/src/arch/commands/archctl" launch tui focus nvim
focus_elapsed=$((SECONDS - focus_started))
(( focus_elapsed < 6 )) || fail "launch-tui focus bounds an unresponsive compositor query" "${focus_elapsed}s"
[[ $(<"$setsid_calls") == $'<uwsm-app>\n<-->\n<xdg-terminal-exec>\n<--app-id=org.arch.nvim>\n<-e>\n<nvim>' ]] ||
  fail "launch-tui focus launches the command when the compositor query times out" "$(<"$setsid_calls")"
pass "launch-tui focus bounds a stalled compositor query before launching the command"

printf 'code\n' >"$fake_home/.local/state/arch/defaults/editor"
cat >"$mock_bin/code" <<'STUB'
#!/bin/bash

exit 0
STUB
chmod +x "$mock_bin/code"

HOME="$fake_home" PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_SETSID_CALLS="$setsid_calls" \
  "$ROOT/src/arch/commands/arch-launch-editor" -cquit

setsid_argv=$(<"$setsid_calls")
[[ $setsid_argv == $'<uwsm-app>\n<-->\n<code>\n<-->\n<-cquit>' ]] ||
  fail "launch-editor separates a graphical editor path from editor options" "$setsid_argv"
pass "launch-editor separates a graphical editor path from editor options"

hook_home="$test_tmp/hook-home"
printf '#!/bin/bash\n' >"$test_tmp/--help"
hook_directory="$hook_home/.config/arch/hooks/post-update.d"
protected_file="$test_tmp/protected"
mkdir -p "$hook_directory"
printf 'protected\n' >"$protected_file"
ln -s "$protected_file" "$hook_directory/--help"
(
  cd -- "$test_tmp"
  HOME="$hook_home" AP="$ROOT" "$ROOT/src/arch/commands/archctl" hook install post-update ./--help >"$test_tmp/hook-install-output"
)
[[ -f $hook_directory/--help && ! -L $hook_directory/--help ]] || fail "hook-install replaces a destination symlink itself"
[[ $(<"$protected_file") == protected ]] || fail "hook-install does not overwrite the symlink target"
[[ $(stat -c '%a' "$hook_directory/--help") == 755 ]] || fail "hook-install marks the installed hook executable"
pass "hook-install treats a dash-prefixed source as an operand and atomically replaces symlinks"
