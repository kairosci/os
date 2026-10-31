#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

export AP="$ROOT"

if "$ARCH_TEST_CLI_BIN/arch-cmd-present" -p; then
  fail "cmd-present treats an option-shaped command name literally"
fi
pass "cmd-present treats an option-shaped command name literally"

"$ARCH_TEST_CLI_BIN/arch-cmd-missing" -p ||
  fail "cmd-missing treats an option-shaped command name literally"
pass "cmd-missing treats an option-shaped command name literally"

"$ARCH_TEST_CLI_BIN/arch-cmd-present" bash || fail "cmd-present still finds an ordinary command"
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

if [[ -n ${ARCH_TEST_PACKAGE_CALLS:-} ]]; then
  exit 0
elif [[ ${1:-} == "--" ]]; then
  shift
  [[ ${1:-} == "installed" ]]
elif [[ ${1:-} == "--help" ]]; then
  exit 0
else
  [[ ${1:-} == "installed" ]]
fi
STUB
chmod +x "$mock_bin/pacman"

if PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/arch-pkg-present" --help; then
  fail "pkg-present treats an option-shaped package name literally"
fi
pass "pkg-present treats an option-shaped package name literally"

PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/arch-pkg-missing" --help ||
  fail "pkg-missing treats an option-shaped package name literally"
pass "pkg-missing treats an option-shaped package name literally"

PATH="$mock_bin:$PATH" "$ROOT/src/arch/commands/arch-pkg-present" installed ||
  fail "pkg-present still finds an installed package"
pass "pkg-present still finds an installed package"

package_calls="$test_tmp/package-calls"
cat >"$mock_bin/arch-pkg-missing" <<'STUB'
#!/bin/bash

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
chmod +x "$mock_bin/arch-pkg-missing" "$mock_bin/sudo" "$mock_bin/yay"

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

if PATH="$mock_bin:$PATH" "$ARCH_TEST_CLI_BIN/arch-hw-match" --help; then
  fail "hw-match treats an option-shaped hardware pattern literally"
fi
pass "hw-match treats an option-shaped hardware pattern literally"

PATH="$mock_bin:$PATH" "$ARCH_TEST_CLI_BIN/arch-hw-match" known-hardware ||
  fail "hw-match still accepts an ordinary hardware pattern"
pass "hw-match still accepts an ordinary hardware pattern"

pkill_calls="$test_tmp/pkill-calls"
setsid_calls="$test_tmp/setsid-calls"
cat >"$mock_bin/pkill" <<'STUB'
#!/bin/bash

: "${ARCH_TEST_PKILL_CALLS:?}"
printf '<%s>\n' "$@" >"$ARCH_TEST_PKILL_CALLS"
STUB
cat >"$mock_bin/setsid" <<'STUB'
#!/bin/bash

if [[ -n ${ARCH_TEST_SETSID_CALLS:-} ]]; then
  printf '<%s>\n' "$@" >"$ARCH_TEST_SETSID_CALLS"
fi
exit 0
STUB
chmod +x "$mock_bin/pkill" "$mock_bin/setsid"

PATH="$mock_bin:$ARCH_TEST_CLI_BIN:$PATH" ARCH_TEST_PKILL_CALLS="$pkill_calls" \
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
if PATH="$mock_bin:$ARCH_TEST_CLI_BIN:$PATH" ARCH_TEST_PKILL_CALLS="$pkill_calls" \
  ARCH_TEST_SETSID_CALLS="$setsid_calls" "$ARCH_TEST_CLI_BIN/arch-restart-app" >/dev/null 2>&1; then
  fail "restart-app rejects a missing application name"
fi
[[ ! -s $pkill_calls && ! -s $setsid_calls ]] ||
  fail "restart-app validates arguments before stopping or launching processes"
pass "restart-app validates arguments before stopping or launching processes"
: >"$pkill_calls"
: >"$setsid_calls"
PATH="$mock_bin:$ARCH_TEST_CLI_BIN:$PATH" ARCH_TEST_PKILL_CALLS="$pkill_calls" \
  ARCH_TEST_SETSID_CALLS="$setsid_calls" "$ARCH_TEST_CLI_BIN/arch-restart-hyprsunset"
[[ $(<"$pkill_calls") == $'<-x>\n<-->\n<hyprsunset>' && \
  $(<"$setsid_calls") == $'<uwsm-app>\n<-->\n<hyprsunset>' ]] ||
  fail "the hidden hyprsunset compatibility entrypoint uses the shared restart module"
pass "the hidden hyprsunset compatibility entrypoint uses the shared restart module"

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

cat >"$mock_bin/arch-launch-tui" <<'STUB'
#!/bin/bash

: "${ARCH_TEST_EDITOR_CALLS:?}"
printf '<%s>\n' "$@" >"$ARCH_TEST_EDITOR_CALLS"
STUB
chmod +x "$mock_bin/arch-launch-tui"

HOME="$fake_home" PATH="$mock_bin:$ROOT/src/arch/commands:$PATH" ARCH_TEST_EDITOR_CALLS="$editor_calls" \
  "$ROOT/src/arch/commands/arch-launch-editor" -cquit

editor_argv=$(<"$editor_calls")
[[ $editor_argv == $'<nvim>\n<-->\n<-cquit>' ]] ||
  fail "launch-editor separates a terminal editor path from editor options" "$editor_argv"
pass "launch-editor separates a terminal editor path from editor options"

setsid_calls="$test_tmp/setsid-calls"
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
  HOME="$hook_home" AP="$ROOT" "$ARCH_TEST_CLI_BIN/arch-hook-install" post-update --help >"$test_tmp/hook-install-output"
)
[[ -f $hook_directory/--help && ! -L $hook_directory/--help ]] || fail "hook-install replaces a destination symlink itself"
[[ $(<"$protected_file") == protected ]] || fail "hook-install does not overwrite the symlink target"
[[ $(stat -c '%a' "$hook_directory/--help") == 755 ]] || fail "hook-install marks the installed hook executable"
pass "hook-install treats a dash-prefixed source as an operand and atomically replaces symlinks"
