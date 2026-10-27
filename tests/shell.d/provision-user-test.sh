#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

mock_bin="$test_tmp/bin"
mkdir -p "$mock_bin" "$test_tmp/home" "$test_tmp/home/.hermes/profiles/james"
test_arch_path="$test_tmp/arch"
mkdir -p "$test_arch_path/src/python/installer_user"
ln -s "$ROOT/src/commands" "$test_arch_path/src/commands"
ln -s "$ROOT/src/cli" "$test_arch_path/src/cli"
ln -s "$ROOT/data" "$test_arch_path/data"
mkdir -p "$test_arch_path/applications"
printf '[Desktop Entry]\nName=Provisioning test\nType=Application\n' >"$test_arch_path/applications/provisioning-test.desktop"
ln -s "$ROOT/default" "$test_arch_path/default"
cat >"$test_arch_path/src/python/installer_user/all.py" <<'PY'
import os
from pathlib import Path

Path(os.environ["TEST_SETUP_CALLED"]).touch()
PY
export TEST_SETUP_CALLED="$test_tmp/setup-called"

for command in xdg-user-dirs-update xdg-settings xdg-mime update-desktop-database; do
  printf '#!/bin/bash\nprintf "%%s %%s\\n" "${0##*/}" "$*" >>"$TEST_COMMAND_LOG"\n' >"$mock_bin/$command"
done
export TEST_COMMAND_LOG=$test_tmp/commands.log
chmod +x "$mock_bin"/*

setup_arch_path="$test_tmp/setup-arch"
setup_bin="$test_tmp/setup-bin"
mkdir -p "$setup_arch_path/data/installer" "$setup_arch_path/src/python/installer_user/setup" "$setup_bin"
cat >"$setup_arch_path/data/installer/user-setup.yml" <<'YAML'
steps:
  - setup/first.py
  - setup/second.py
  - setup/third.py
YAML
for step in first second third; do
  : >"$setup_arch_path/src/python/installer_user/setup/$step.py"
done
cat >"$setup_bin/python3" <<'SH'
#!/bin/bash
printf '%s\n' "$2" >>"$TEST_SETUP_LOG"
if [[ ${TEST_FAIL_STEP:-} == "${2##*/}" ]]; then
  exit 7
fi
SH
chmod +x "$setup_bin/python3"
export TEST_SETUP_LOG="$test_tmp/setup-steps.log"

ARCH_PATH="$setup_arch_path" PATH="$setup_bin:$PATH" /usr/bin/python3 -I \
  "$ROOT/src/python/installer_user/all.py" || fail "Python setup orchestrator succeeds"
[[ $(<"$TEST_SETUP_LOG") == "$setup_arch_path/src/python/installer_user/setup/first.py
$setup_arch_path/src/python/installer_user/setup/second.py
$setup_arch_path/src/python/installer_user/setup/third.py" ]] ||
  fail "Python setup orchestrator preserves YAML step order"
pass "Python setup orchestrator preserves YAML step order"

setup_count=$(ARCH_PATH="$setup_arch_path" /usr/bin/python3 -I \
  "$ROOT/src/python/installer_user/all.py" --count)
[[ $setup_count == 3 ]] || fail "Python setup orchestrator reports its configured step count"
pass "Python setup orchestrator reports its configured step count"

production_setup_count=$(ARCH_PATH="$ROOT" /usr/bin/python3 -I \
  "$ROOT/src/python/installer_user/all.py" --count)
(( production_setup_count > 0 )) || fail "packaged setup data references existing Python setup steps"
pass "packaged setup data references existing Python setup steps"

: >"$TEST_SETUP_LOG"
if ARCH_PATH="$setup_arch_path" PATH="$setup_bin:$PATH" TEST_FAIL_STEP=second.py \
  /usr/bin/python3 -I "$ROOT/src/python/installer_user/all.py"; then
  fail "Python setup orchestrator stops after a failed setup step"
else
  [[ $? == 7 ]] || fail "Python setup orchestrator preserves the failing step's status"
fi
[[ $(<"$TEST_SETUP_LOG") == "$setup_arch_path/src/python/installer_user/setup/first.py
$setup_arch_path/src/python/installer_user/setup/second.py" ]] ||
  fail "Python setup orchestrator does not run steps after a failure"
pass "Python setup orchestrator stops after a failed setup step"

# Provisioning prepends $ARCH_PATH/src/cli, which shadows a mock for anything
# os ships, so its Python setup orchestrator is stubbed under the test root.

HOME="$test_tmp/home" PATH="$mock_bin:$ROOT/src/commands:$PATH" ARCH_PATH="$test_arch_path" \
  ARCH_INSTALL="$test_tmp/installer" bash "$ROOT/src/commands/arch-provision-user" >/dev/null ||
  fail "arch-provision-user finishes"

[[ -f $TEST_SETUP_CALLED ]] || fail "arch-provision-user runs the Python user setup orchestrator"
pass "arch-provision-user runs the Python user setup orchestrator"

[[ ! -e $test_tmp/home/.agents/skills && ! -e $test_tmp/home/.claude/skills &&
  ! -e $test_tmp/home/.codex/skills && ! -e $test_tmp/home/.pi/agent/skills &&
  ! -e $test_tmp/home/.gemini/config/skills && ! -e $test_tmp/home/.hermes/skills ]] ||
  fail "arch-provision-user still creates agent skill directories"
pass "arch-provision-user does not provision agent skill directories"

for dir in DOWNLOAD:Downloads PICTURES:Pictures VIDEOS:Videos DOCUMENTS:Documents MUSIC:Music; do
  grep -qxF "xdg-user-dirs-update --set ${dir%%:*} $test_tmp/home/${dir#*:}" "$TEST_COMMAND_LOG" ||
    fail "provisioning names the ${dir%%:*} folder in English" "$(cat "$TEST_COMMAND_LOG")"
done
for dir in Downloads Pictures Videos Documents Music; do
  [[ -d $test_tmp/home/$dir ]] || fail "provisioning creates the $dir folder it names"
done
pass "provisioning names the user folders in English before a first login in another language"

: >"$TEST_COMMAND_LOG"
mkdir -p "$test_tmp/home/.config"
printf 'XDG_DOWNLOAD_DIR="$HOME/下载"\n' >"$test_tmp/home/.config/user-dirs.dirs"
HOME="$test_tmp/home" PATH="$mock_bin:$ROOT/src/commands:$PATH" ARCH_PATH="$test_arch_path" \
  ARCH_INSTALL="$test_tmp/installer" bash "$ROOT/src/commands/arch-provision-user" --force >/dev/null ||
  fail "arch-provision-user finishes again"
! grep -q -- '--set DOWNLOAD ' "$TEST_COMMAND_LOG" || fail "provisioning keeps a folder the user already named"
grep -q -- '--set PICTURES ' "$TEST_COMMAND_LOG" || fail "provisioning still names the folders the user has not"
pass "provisioning keeps a folder the user already named, in any language"
