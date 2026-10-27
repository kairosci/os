#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

# Root never reads the fixture root, so as root the build and first boot below
# would act on this machine. A skip is a pass.
if (( EUID == 0 )); then
  skip "running as root, where image setup ignores fixture roots; skipping"
  exit 0
fi

umask 022
test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

unit_name=arch-provision-hardware.service
unit_source="$ROOT/installer/provisioning/$unit_name"

# arch-apply-hardware refuses anyone but root, and root never reads the
# fixture root. Run a copy whose only change is that check, so a normal user
# can build an image into a fixture root.
apply_hardware="$test_tmp/arch-apply-hardware"
sed 's/^if (( EUID != 0 )); then$/if false; then/' "$ROOT/src/cli/arch-apply-hardware" >"$apply_hardware"
chmod +x "$apply_hardware"
grep -q '^if false; then$' "$apply_hardware" || fail "the test copy of arch-apply-hardware drops only its root check"

# Commands a hardware leaf would reach for. Any call means a leaf ran.
stub_bin="$test_tmp/stub-bin"
mkdir -p "$stub_bin"
for command in sudo pacman pacman-key systemctl lspci arch-pkg-add modinfo; do
  cat >"$stub_bin/$command" <<'SH'
#!/bin/bash
printf '%s %s\n' "${0##*/}" "$*" >>"$LEAF_CALLS"
exit 1
SH
done
cat >"$stub_bin/bootctl" <<'SH'
#!/bin/bash
printf 'Current Boot Loader:\n    Product: Limine\n'
SH
chmod +x "$stub_bin/bootctl"
stub_rebuild() {
  cat >"$stub_bin/$1" <<'SH'
#!/bin/bash
printf '%s %s\n' "${0##*/}" "$*" >>"$REBUILDS"
SH
  chmod +x "$stub_bin/$1"
}
stub_rebuild mkinitcpio
# Only the stubs count as present, so a machine with Limine never runs its own
# limine-mkinitcpio here.
cat >"$stub_bin/arch-cmd-present" <<SH
#!/bin/bash
[[ -x $stub_bin/\$1 ]]
SH
chmod +x "$stub_bin"/*
export LEAF_CALLS="$test_tmp/leaf-calls" REBUILDS="$test_tmp/rebuilds"

fake_platform "$test_tmp/hw" aarch64-apple
base_path="$test_tmp/hw/bin:$stub_bin:$ROOT/src/cli:/usr/local/bin:/usr/bin:/bin"

# An os tree whose hardware setup is three leaves that log their runs.
# Leaves a and b write initramfs drop-ins; b then fails while $FAIL_B exists.
fixture="$test_tmp/arch"
mkdir -p "$fixture/installer/helpers" "$fixture/installer/provisioning" "$fixture/installer/hardware/apple" "$fixture/src/cli"
cp "$ROOT/installer/helpers/logging.sh" "$ROOT/installer/helpers/image-target.sh" "$fixture/installer/helpers/"
cp "$unit_source" "$fixture/installer/provisioning/"
cat >"$fixture/installer/hardware/all.sh" <<'SH'
run_logged "$ARCH_INSTALL/hardware/a.sh"
run_logged "$ARCH_INSTALL/hardware/apple/b.sh"
run_logged "$ARCH_INSTALL/hardware/c.sh"
SH
cat >"$fixture/installer/hardware/a.sh" <<'SH'
printf 'a user=%s path=%s\n' "${ARCH_INSTALL_USER-unset}" "$ARCH_PATH" >>"$RUNS"
mkdir -p "$ARCH_IMAGE_ROOT/etc/mkinitcpio.conf.d"
echo 'MODULES+=(a)' >"$ARCH_IMAGE_ROOT/etc/mkinitcpio.conf.d/a.conf"
SH
cat >"$fixture/installer/hardware/apple/b.sh" <<'SH'
mkdir -p "$ARCH_IMAGE_ROOT/etc/mkinitcpio.conf.d"
echo 'MODULES+=(b)' >"$ARCH_IMAGE_ROOT/etc/mkinitcpio.conf.d/b.conf"
[[ ! -e $FAIL_B ]] || return 1
echo b >>"$RUNS"
SH
cat >"$fixture/installer/hardware/c.sh" <<'SH'
echo c >>"$RUNS"
[[ ! -e $REQUEST_REBUILD ]] || touch "$ARCH_IMAGE_BOOT_REBUILD"
SH
export RUNS="$test_tmp/runs" FAIL_B="$test_tmp/fail-b" REQUEST_REBUILD="$test_tmp/request-rebuild"

new_root() {
  local root="$test_tmp/root-$1"
  rm -rf "$root"
  mkdir -p "$root/var/log"
  printf '%s\n' "$root"
}

write_manifest() {
  local root=$1 body=${2:-$'format=1\nplatform=aarch64-apple\n'}
  mkdir -p "$root/var/lib/arch/image"
  chmod 0755 "$root/var/lib/arch/image"
  printf '%s' "$body" >"$root/var/lib/arch/image/target"
  chmod 0644 "$root/var/lib/arch/image/target"
}

build() {
  local root=$1 arch=${2:-$fixture}
  local install_dir=${3:-$arch/installer}
  ARCH_IMAGE_ROOT="$root" ARCH_PATH="$arch" ARCH_INSTALL="$install_dir" ARCH_INSTALL_LOG_FILE="$root/var/log/arch-install.log" \
    PATH="$base_path" "$apply_hardware" --defer-provisioning
}

first_boot() {
  local root=$1
  ARCH_IMAGE_ROOT="$root" ARCH_PATH="$fixture" ARCH_PROC_ROOT="$test_tmp/hw/proc" \
    PATH="$base_path" "$ROOT/src/cli/arch-provision-hardware"
}

reset_logs() {
  rm -f "$RUNS" "$LEAF_CALLS" "$REBUILDS" "$FAIL_B"
}

queue_of() {
  cat "$1/var/lib/arch/image/deferred-steps"
}

# --- The build ---------------------------------------------------------------

# The real hardware setup: every leaf is queued in order and none of them runs.
reset_logs
root=$(new_root real)
write_manifest "$root"
output=$(build "$root" "$ROOT" "$ROOT/installer") || fail "an image build defers the real hardware setup" "$output"
expected=$(python3 - "$ROOT/installer/hardware/all.sh" <<'PY'
import re
import sys
from pathlib import Path

for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
  shell_step = re.fullmatch(r'run_logged "\$ARCH_INSTALL/(hardware/.+\.sh)"', line)
  python_step = re.fullmatch(r'run_logged "\$ARCH_PATH/src/python/(installer/hardware/.+\.py)"', line)
  if shell_step:
    print("installer/" + shell_step.group(1))
  elif python_step:
    print("src/python/" + python_step.group(1))
PY
)
[[ -n $expected && $(queue_of "$root") == "$expected" ]] ||
  fail "an image build queues every hardware leaf in order" "expected:
$expected
queued:
$(queue_of "$root")"
[[ ! -e $LEAF_CALLS ]] || fail "an image build runs no hardware leaf" "$(cat "$LEAF_CALLS")"
[[ $output == *"Image build for aarch64-apple: deferred $(wc -l <<<"$expected") hardware steps to first boot"* ]] ||
  fail "an image build reports what it deferred" "$output"
pass "an image build queues every hardware leaf in order and runs none of them"

[[ $(<"$unit_source") == "$(<"$root/etc/systemd/system/$unit_name")" ]] ||
  fail "an image build installs the first-boot hardware service"
[[ $(readlink "$root/etc/systemd/system/multi-user.target.wants/$unit_name") == "/etc/systemd/system/$unit_name" ]] ||
  fail "an image build enables the first-boot hardware service"
[[ -f $root/var/lib/arch/image/target && ! -e $root/var/lib/arch/image/target.booted ]] ||
  fail "an image build leaves its manifest for the first boot"
[[ $(stat -c '%a' "$root/var/lib/arch/image/deferred-steps") == "644" ]] ||
  fail "the queue is readable and only its owner writes it"
pass "an image build arms the first-boot hardware service"

before=$(queue_of "$root")
build "$root" "$ROOT" "$ROOT/installer" >/dev/null || fail "an image build can run hardware setup again"
[[ $(queue_of "$root") == "$before" ]] || fail "running hardware setup again in the build queues the same steps"
pass "running hardware setup again in the build queues the same steps"

# Without a manifest nothing is deferred: the leaves run as they always did.
reset_logs
root=$(new_root live)
build "$root" >/dev/null || fail "hardware setup without a manifest runs"
[[ $(cat "$RUNS") == $'a user= path='"$fixture"$'\nb\nc' ]] || fail "hardware setup without a manifest runs every leaf" "$(cat "$RUNS")"
[[ ! -e $root/var/lib/arch/image && ! -e $root/etc/systemd/system/$unit_name ]] ||
  fail "hardware setup without a manifest queues and arms nothing"
pass "hardware setup without a manifest runs every leaf and defers nothing"

# Hardware setup that has to wait for a first boot in progress decides only
# once it has the lock: by then the manifest is retired and the leaves run here.
reset_logs
root=$(new_root race)
write_manifest "$root"
(
  exec {lock}>>"$root/var/lib/arch/image/lock"
  flock "$lock"
  touch "$test_tmp/locked"
  until [[ -e $test_tmp/release || ! -d $test_tmp ]]; do sleep 0.1; done
  mv "$root/var/lib/arch/image/target" "$root/var/lib/arch/image/target.booted"
) &
first_boot_pid=$!
until [[ -e $test_tmp/locked ]]; do sleep 0.1; done
build "$root" >/dev/null &
setup_pid=$!
sleep 1
kill -0 "$setup_pid" 2>/dev/null || fail "hardware setup waits while a first boot holds the lock"
touch "$test_tmp/release"
wait "$first_boot_pid"
wait "$setup_pid" || fail "hardware setup runs after waiting for a first boot"
[[ $(cat "$RUNS") == $'a user= path='"$fixture"$'\nb\nc' && ! -e $root/var/lib/arch/image/deferred-steps ]] ||
  fail "hardware setup that waited for a first boot runs its leaves instead of queueing them"
pass "hardware setup waits for a first boot in progress and then runs on the machine"

# A manifest that is not unambiguously root's own stops hardware setup outright.
check_refused() {
  local description=$1 root=$2
  reset_logs
  if build "$root" >/dev/null 2>&1; then
    fail "hardware setup refuses $description"
  fi
  [[ ! -e $RUNS && ! -e $root/var/lib/arch/image/deferred-steps && ! -e $root/etc/systemd/system/$unit_name ]] ||
    fail "hardware setup refuses $description without running, queueing or arming anything"
  pass "hardware setup refuses $description"
}

root=$(new_root format)
write_manifest "$root" $'format=2\nplatform=aarch64-apple\n'
check_refused "a manifest of an unknown format" "$root"

root=$(new_root platform)
write_manifest "$root" $'format=1\nplatform=apple\n'
check_refused "a manifest naming an unknown platform" "$root"

root=$(new_root malformed)
write_manifest "$root" $'format=1\napple-silicon\n'
check_refused "a malformed manifest" "$root"

root=$(new_root writable)
write_manifest "$root"
chmod 0666 "$root/var/lib/arch/image/target"
check_refused "a manifest others can write" "$root"

root=$(new_root writable-dir)
write_manifest "$root"
chmod 0777 "$root/var/lib/arch/image"
check_refused "a manifest in a directory others can write" "$root"

root=$(new_root symlink)
write_manifest "$root"
mv "$root/var/lib/arch/image/target" "$root/var/lib/arch/image/real-target"
ln -s real-target "$root/var/lib/arch/image/target"
check_refused "a symlinked manifest" "$root"

# --- The first boot ----------------------------------------------------------

reset_logs
root=$(new_root fresh)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
[[ $(queue_of "$root") == $'installer/hardware/a.sh\ninstaller/hardware/apple/b.sh\ninstaller/hardware/c.sh' ]] ||
  fail "the fixture image queues its three leaves" "$(queue_of "$root")"

output=$(first_boot "$root") || fail "the first boot finishes the deferred hardware setup" "$output"
[[ $(cat "$RUNS") == $'a user= path='"$fixture"$'\nb\nc' ]] ||
  fail "the first boot runs each deferred leaf once, in order, with no install user" "$(cat "$RUNS")"
[[ $output == *"First boot of an image built for aarch64-apple, on aarch64-apple hardware"* ]] ||
  fail "the first boot reports the image target and the live platform" "$output"
[[ ! -e $root/var/lib/arch/image/target && -f $root/var/lib/arch/image/target.booted ]] ||
  fail "the first boot retires the build manifest"
[[ ! -e $root/var/lib/arch/image/deferred-steps ]] || fail "the first boot empties the queue"
[[ ! -L $root/etc/systemd/system/multi-user.target.wants/$unit_name && -f $root/etc/systemd/system/$unit_name ]] ||
  fail "the first boot disables its service and keeps the unit, so a start job already queued is skipped rather than failed"
[[ $(cat "$REBUILDS") == "mkinitcpio -P" ]] ||
  fail "the first boot rebuilds the initramfs once after a leaf changed it" "$(cat "$REBUILDS" 2>/dev/null)"
[[ ! -e $root/var/lib/arch/image/initramfs-inputs ]] || fail "the first boot clears the rebuild it owed"
grep -q 'Completed: .*/installer/hardware/c.sh' "$root/var/log/arch-install.log" ||
  fail "the first boot logs each step to the install log"
pass "the first boot runs the deferred hardware setup with no command from the owner"

rm -f "$RUNS" "$REBUILDS"
output=$(first_boot "$root") || fail "running the first-boot hardware setup again succeeds"
[[ -z $output && ! -e $RUNS && ! -e $REBUILDS ]] ||
  fail "running the first-boot hardware setup again does nothing" "$output"
pass "running the first-boot hardware setup again does nothing"

# The live platform is asked once the manifest is retired, so it is the
# hardware's even where the detector cannot tell a booted root (this fixture
# runs no systemd): an Apple Silicon image booted in a VM reports plain aarch64.
fake_platform "$test_tmp/vm" aarch64
reset_logs
root=$(new_root vm)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds for a VM boot"
output=$(ARCH_IMAGE_ROOT="$root" ARCH_PATH="$fixture" ARCH_PROC_ROOT="$test_tmp/vm/proc" \
  PATH="$test_tmp/vm/bin:$stub_bin:$ROOT/src/cli:/usr/local/bin:/usr/bin:/bin" "$ROOT/src/cli/arch-provision-hardware") ||
  fail "the first boot on other hardware finishes" "$output"
[[ $output == *"First boot of an image built for aarch64-apple, on aarch64 hardware"* ]] ||
  fail "the first boot reports the hardware it runs on, not the image target" "$output"
pass "the first boot reports the hardware it runs on, not the image target"

# A failed step stays queued with everything after it; the next boot resumes there.
reset_logs
root=$(new_root resume)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
# A repository without a sync database, which the image never has: the failed
# step is not retried after a fetch.
mkdir -p "$root/etc"
printf '[options]\nArchitecture = auto\n\n[core]\nServer = https://mirror.invalid/$arch/$repo\n' >"$root/etc/pacman.conf"
touch "$FAIL_B"
status=0
output=$(first_boot "$root" 2>&1) || status=$?
(( status == 75 )) || fail "a failed step exits 75, so a platform first boot can tell it from a refusal" "status $status: $output"
[[ $output == *"Deferred hardware step failed: installer/hardware/apple/b.sh"* ]] ||
  fail "the first boot names the failed step" "$output"
[[ $(cat "$RUNS") == "a user= path=$fixture" ]] || fail "the first boot stops at the failed step" "$(cat "$RUNS")"
[[ $(queue_of "$root") == $'installer/hardware/apple/b.sh\ninstaller/hardware/c.sh' ]] ||
  fail "the failed step and those after it stay queued" "$(queue_of "$root")"
[[ -f $root/var/lib/arch/image/target.booted && ! -e $root/var/lib/arch/image/target ]] ||
  fail "the machine stops being an image build once its first boot starts"
[[ -L $root/etc/systemd/system/multi-user.target.wants/$unit_name && -e $root/var/lib/arch/image/initramfs-inputs && ! -e $REBUILDS ]] ||
  fail "the service stays armed and the initramfs rebuild stays owed until the queue is empty"
[[ ! -e $LEAF_CALLS ]] || fail "a failed step fetches no package databases" "$(cat "$LEAF_CALLS")"
pass "a failed step stays queued with the steps after it"

rm -f "$FAIL_B" "$RUNS"
stub_rebuild limine-mkinitcpio
output=$(first_boot "$root") || fail "the next boot finishes the deferred hardware setup" "$output"
[[ $(cat "$RUNS") == $'b\nc' ]] || fail "the next boot resumes at the failed step" "$(cat "$RUNS")"
[[ $(cat "$REBUILDS") == "limine-mkinitcpio " ]] ||
  fail "the next boot rebuilds the initramfs the earlier boot owed, through Limine when present" "$(cat "$REBUILDS" 2>/dev/null)"
[[ ! -e $root/var/lib/arch/image/deferred-steps && ! -L $root/etc/systemd/system/multi-user.target.wants/$unit_name ]] ||
  fail "the next boot disarms the service"
pass "the next boot resumes at the failed step and finishes"

# The step that changed the initramfs inputs is the one that failed: its rerun
# changes nothing more, and the rebuild is still owed.
reset_logs
rm -f "$stub_bin/limine-mkinitcpio"
root=$(new_root rebuild)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
printf '%s\n' installer/hardware/apple/b.sh installer/hardware/c.sh >"$root/var/lib/arch/image/deferred-steps"
touch "$FAIL_B"
first_boot "$root" >/dev/null 2>&1 && fail "the first boot reports the failed step"
rm -f "$FAIL_B"
first_boot "$root" >/dev/null || fail "the next boot finishes the deferred hardware setup"
[[ $(cat "$RUNS") == $'b\nc' && $(cat "$REBUILDS" 2>/dev/null) == "mkinitcpio -P" ]] ||
  fail "a step that changed the initramfs and then failed still gets it rebuilt" "$(cat "$REBUILDS" 2>/dev/null)"
pass "a step that changed the initramfs and then failed still gets it rebuilt"

# A step that only adds to the kernel command line Limine's entry tool builds
# (as intel/fred.sh does) gets the rebuild too.
reset_logs
root=$(new_root cmdline)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
cat >"$fixture/installer/hardware/cmdline.sh" <<'SH'
mkdir -p "$ARCH_IMAGE_ROOT/etc/limine-entry-tool.d"
echo 'KERNEL_CMDLINE[default]+=" example=on"' >"$ARCH_IMAGE_ROOT/etc/limine-entry-tool.d/example.conf"
SH
printf '%s\n' installer/hardware/cmdline.sh >"$root/var/lib/arch/image/deferred-steps"
first_boot "$root" >/dev/null || fail "a step that changes the kernel command line finishes"
[[ $(cat "$REBUILDS" 2>/dev/null) == "mkinitcpio -P" ]] ||
  fail "a step that only changed Limine's kernel command line gets the rebuild" "$(cat "$REBUILDS" 2>/dev/null)"
rm -f "$fixture/installer/hardware/cmdline.sh"
pass "a step that only changed Limine's kernel command line gets the rebuild"

# Module options reach the initramfs through mkinitcpio's modconf hook, so a
# step that only writes /etc/modprobe.d (as nvidia.py does) gets the rebuild too.
reset_logs
root=$(new_root modprobe)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
cat >"$fixture/installer/hardware/modprobe.sh" <<'SH'
mkdir -p "$ARCH_IMAGE_ROOT/etc/modprobe.d"
echo 'options example flag=1' >"$ARCH_IMAGE_ROOT/etc/modprobe.d/example.conf"
SH
printf '%s\n' installer/hardware/modprobe.sh >"$root/var/lib/arch/image/deferred-steps"
first_boot "$root" >/dev/null || fail "a step that changes module options finishes"
[[ $(cat "$REBUILDS" 2>/dev/null) == "mkinitcpio -P" ]] ||
  fail "a step that only changed module options gets the rebuild" "$(cat "$REBUILDS" 2>/dev/null)"
rm -f "$fixture/installer/hardware/modprobe.sh"
pass "a step that only changed module options gets the rebuild"

# --- The pacman keyring -------------------------------------------------------

# Install finalization makes the pacman keyring on plain aarch64.
# An image build asks for it instead, so every machine flashed from the image
# makes its own master key on its first boot, before any step installs a package.
keyring_bin="$test_tmp/keyring-bin"
mkdir -p "$keyring_bin" "$fixture/src/python/installer/post_install" "$fixture/src/python/installer/hardware" \
  "$fixture/data/installer/hardware" "$fixture/data/installer"
# Finalization's repositories are pacman-templates-test.sh's; here they land in
# the root under test, never the host's /etc.
cp "$ROOT/installer/helpers/pacman.sh" "$fixture/installer/helpers/pacman.sh"
cp "$ROOT/src/python/installer/post_install/pacman.py" "$fixture/src/python/installer/post_install/"
cp "$ROOT/data/installer/post-install.yml" "$fixture/data/installer/"
cp "$ROOT/src/python/installer/hardware/pacman_repositories.py" "$fixture/src/python/installer/hardware/"
cp "$ROOT/data/installer/hardware/pacman-repositories.yml" "$fixture/data/installer/hardware/"
cp "$ROOT/src/cli/arch-apply-pacman" "$fixture/src/cli/arch-apply-pacman"
mkdir -p "$fixture/default"
cp -r "$ROOT/default/pacman" "$ROOT/default/regions" "$fixture/default/"
for command in pacman-key arch-pkg-add; do
  cat >"$keyring_bin/$command" <<'SH'
#!/bin/bash
printf '%s %s\n' "${0##*/}" "$*" >>"$KEYRING"
[[ ${0##*/} != "pacman-key" || ! -e $KEYRING_FAIL ]]
SH
done
printf '#!/bin/bash\necho "$PLATFORM"\n' >"$keyring_bin/arch-hw-platform"
printf '#!/bin/bash\nexit 0\n' >"$keyring_bin/lspci"
chmod +x "$keyring_bin"/*
export KEYRING="$test_tmp/keyring" KEYRING_FAIL="$test_tmp/keyring-fail"
request=var/lib/arch/image/pacman-keyring

security_test_status=0
ARCH_PATH="$ROOT" PACMAN_TEST_ROOT="$test_tmp" python3 -I - "$ROOT/src/python/installer/post_install/pacman.py" <<'PY' || security_test_status=$?
import os
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

module = runpy.run_path(sys.argv[1])
config = module["settings"]()[1]
root = Path(os.environ["PACMAN_TEST_ROOT"]) / "keyring-symlink"
image = root / config["image"]["directory"]
image.mkdir(parents=True)
target = root / "attacker-controlled"
target.write_text("preserve this", encoding="utf-8")
request = image / config["image"]["keyring_request"]
request.symlink_to(target)
with patch.object(module["os"], "geteuid", return_value=os.getuid()):
  try:
    module["request_image_keyring"](root, config)
  except ValueError:
    pass
  else:
    raise SystemExit("a symlinked keyring request was accepted")
assert target.read_text(encoding="utf-8") == "preserve this"
with patch.object(module["os"], "geteuid", return_value=os.getuid()):
  with patch.dict(module["os"].environ, {"ARCH_IMAGE_ROOT": "", "LANG": "en_US.UTF-8"}):
    try:
      module["image_root"](config)
    except PermissionError as error:
      assert str(error) == config["messages"]["en"]["image_root_required"]
    else:
      raise SystemExit("a non-root image setup without a test root was accepted")
  with patch.dict(module["os"].environ, {"ARCH_IMAGE_ROOT": "", "LANG": "it_IT.UTF-8"}):
    try:
      module["image_root"](config)
    except PermissionError as error:
      assert str(error) == config["messages"]["it"]["image_root_required"]
    else:
      raise SystemExit("a non-root image setup without a test root was accepted")
with patch.object(module["os"], "geteuid", return_value=0):
  with patch.dict(module["os"].environ, {"ARCH_IMAGE_ROOT": str(root)}):
    assert module["image_root"](config) == Path("/")
PY
(( security_test_status == 0 )) ||
  fail "pacman finalization does not follow a planted keyring-request symlink and ignores fixture paths as root"
pass "pacman finalization ignores root fixture overrides and refuses a symlinked keyring request"

finalize() {
  mkdir -p "$1/etc/pacman.d"
  ARCH_IMAGE_ROOT="$1" ARCH_PATH="$fixture" PLATFORM=$2 \
    PATH="$keyring_bin:$base_path" python3 -I "$fixture/src/python/installer/post_install/pacman.py"
}

keyring_boot() {
  ARCH_IMAGE_ROOT="$1" ARCH_PATH="$fixture" ARCH_PROC_ROOT="$test_tmp/hw/proc" \
    PATH="$keyring_bin:$base_path" "$ROOT/src/cli/arch-provision-hardware"
}

for platform in aarch64; do
  rm -f "$KEYRING"
  root=$(new_root "install-$platform")
  finalize "$root" "$platform" || fail "$platform: install finalization succeeds"
  [[ $(cat "$KEYRING") == $'arch-pkg-add archlinuxarm-keyring\npacman-key --init\npacman-key --populate' ]] ||
    fail "$platform: an install makes its pacman keyring in finalization, as before" "$(cat "$KEYRING")"
  [[ ! -e $root/$request ]] || fail "$platform: an install requests no first-boot keyring"

  rm -f "$KEYRING"
  root=$(new_root "image-$platform")
  write_manifest "$root" $'format=1\nplatform='"$platform"$'\n'
  build "$root" >/dev/null || fail "$platform: the fixture image builds"
  finalize "$root" "$platform" || fail "$platform: image finalization succeeds"
  [[ $(cat "$KEYRING") == "arch-pkg-add archlinuxarm-keyring" ]] ||
    fail "$platform: an image build makes no pacman keyring" "$(cat "$KEYRING")"
  [[ -f $root/$request ]] || fail "$platform: an image build asks its first boot for the keyring"
done
for platform in aarch64-apple x86; do
  rm -f "$KEYRING"
  root=$(new_root "image-$platform")
  write_manifest "$root" $'format=1\nplatform='"$platform"$'\n'
  build "$root" >/dev/null || fail "$platform: the fixture image builds"
  finalize "$root" "$platform" || fail "$platform: image finalization succeeds"
  finalize "$(new_root "install-$platform")" "$platform" || fail "$platform: install finalization succeeds"
  [[ ! -e $KEYRING && ! -e $root/$request ]] || fail "$platform: finalization leaves the keyring alone" "$(cat "$KEYRING" 2>/dev/null)"
done
pass "an image build on plain aarch64 leaves the pacman keyring to the first boot"

reset_logs
rm -f "$KEYRING"
root=$(new_root image-aarch64-apple)
write_manifest "$root"
build "$root" >/dev/null || fail "the Mac fixture image builds"
keyring_boot "$root" >/dev/null || fail "a Mac image's first boot finishes"
[[ ! -e $KEYRING ]] || fail "a first boot nobody asked for a keyring leaves the keyring alone" "$(cat "$KEYRING")"
pass "a first boot nobody asked for a keyring leaves the keyring alone"

reset_logs
root=$test_tmp/root-image-aarch64
mkdir -p "$root/etc/pacman.d/gnupg"
touch "$root/etc/pacman.d/gnupg/build-master-key" "$KEYRING_FAIL"
status=0
output=$(KEYRING=$RUNS keyring_boot "$root" 2>&1) || status=$?
(( status == 75 )) || fail "a keyring that can't be made exits 75" "status $status: $output"
[[ $output == *"could not create the pacman keyring"* ]] || fail "the first boot says the keyring failed" "$output"
[[ $(cat "$RUNS") == "pacman-key --gpgdir $root/etc/pacman.d/gnupg --init" ]] ||
  fail "no step runs before the keyring exists" "$(cat "$RUNS")"
[[ -f $root/$request && $(queue_of "$root") == $'installer/hardware/a.sh\ninstaller/hardware/apple/b.sh\ninstaller/hardware/c.sh' ]] ||
  fail "the keyring request and the whole queue stay for the next boot"
pass "a keyring that can't be made stays requested and holds back every step"

rm -f "$KEYRING_FAIL" "$RUNS"
mkdir -p "$root/etc/pacman.d/gnupg"
touch "$root/etc/pacman.d/gnupg/build-master-key"
output=$(KEYRING=$RUNS keyring_boot "$root") || fail "the next boot makes the keyring and finishes" "$output"
[[ $(cat "$RUNS") == "pacman-key --gpgdir $root/etc/pacman.d/gnupg --init"$'\n'"pacman-key --gpgdir $root/etc/pacman.d/gnupg --populate"$'\na user= path='"$fixture"$'\nb\nc' ]] ||
  fail "the first boot makes the keyring, then runs the steps" "$(cat "$RUNS")"
[[ ! -e $root/etc/pacman.d/gnupg/build-master-key ]] || fail "the first boot replaces a keyring the build left"
[[ ! -e $root/$request && ! -e $root/var/lib/arch/image/deferred-steps ]] || fail "the first boot clears the keyring request"
pass "the first boot replaces any build keyring with the machine's own before the steps run"

# A keyring request with nothing queued (a build whose hardware setup queued no
# step) still gets its keyring.
reset_logs
rm -f "$RUNS"
root=$test_tmp/root-keyring-only
mkdir -p "$root/var/lib/arch/image"
install -m 0644 /dev/null "$root/$request"
output=$(KEYRING=$RUNS keyring_boot "$root") || fail "a first boot with only a keyring request finishes" "$output"
[[ $(cat "$RUNS") == "pacman-key --gpgdir $root/etc/pacman.d/gnupg --init"$'\n'"pacman-key --gpgdir $root/etc/pacman.d/gnupg --populate" && ! -e $root/$request ]] ||
  fail "a keyring request is honoured with no queued step" "$(cat "$RUNS" 2>/dev/null)"
grep -qx 'ConditionPathExists=|/var/lib/arch/image/pacman-keyring' "$ROOT/installer/provisioning/arch-provision-hardware.service" ||
  fail "the first-boot unit also starts for a keyring request alone"
pass "a keyring request with no queued step still gets the machine's own keyring"

# A leaf a later os no longer ships is dropped; a queue entry outside the
# hardware setup stops the run before anything runs.
reset_logs
root=$(new_root gone)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
printf '%s\n' installer/hardware/removed.sh installer/hardware/c.sh >"$root/var/lib/arch/image/deferred-steps"
output=$(first_boot "$root") || fail "a step no longer shipped does not block the rest" "$output"
[[ $output == *"Skipping deferred hardware step installer/hardware/removed.sh"* && $(cat "$RUNS") == "c" ]] ||
  fail "a step no longer shipped is skipped and the rest run" "$output"
pass "a deferred step os no longer ships is skipped"

# A step that would build the boot image itself asks for the rebuild after the
# last step instead: one rebuild, even when no
# initramfs input changed, and the request outlives a run that stopped early.
reset_logs
root=$(new_root request)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
printf '%s\n' installer/hardware/c.sh >"$root/var/lib/arch/image/deferred-steps"
first_boot "$root" >/dev/null || fail "a step that asks for nothing finishes"
[[ ! -e $REBUILDS ]] || fail "no rebuild without a changed input or a request" "$(cat "$REBUILDS")"
reset_logs
root=$(new_root request)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
printf '%s\n' installer/hardware/c.sh >"$root/var/lib/arch/image/deferred-steps"
touch "$REQUEST_REBUILD"
first_boot "$root" >/dev/null || fail "a step that asks for the rebuild finishes"
rm -f "$REQUEST_REBUILD"
[[ $(cat "$REBUILDS" 2>/dev/null) == "mkinitcpio -P" && ! -e $root/var/lib/arch/image/boot-rebuild ]] ||
  fail "the request alone, with no changed input, gets one rebuild and is then cleared" "$(cat "$REBUILDS" 2>/dev/null)"
reset_logs
root=$(new_root request)
write_manifest "$root"
build "$root" >/dev/null || fail "the fixture image builds"
printf '%s\n' installer/hardware/c.sh installer/hardware/apple/b.sh >"$root/var/lib/arch/image/deferred-steps"
rm -f "$root/etc/mkinitcpio.conf.d/b.conf"
touch "$REQUEST_REBUILD" "$FAIL_B"
first_boot "$root" >/dev/null 2>&1 && fail "the first boot reports the failed step"
[[ -f $root/var/lib/arch/image/boot-rebuild && ! -e $REBUILDS ]] ||
  fail "a requested rebuild waits for the queue to empty, and stays requested"
rm -f "$FAIL_B" "$REQUEST_REBUILD"
first_boot "$root" >/dev/null || fail "the next boot finishes the deferred hardware setup"
[[ $(cat "$REBUILDS" 2>/dev/null) == "mkinitcpio -P" && ! -e $root/var/lib/arch/image/boot-rebuild ]] ||
  fail "the requested rebuild runs once after the last step and is then cleared" "$(cat "$REBUILDS" 2>/dev/null)"
pass "a step can ask for the one rebuild after the last step"

for entry in /etc/passwd installer/hardware/../../src/cli/x.sh installer/login/sddm.sh \
  src/python/installer/hardware/../../cli/x.py src/python/installer/../../cli/x.py; do
  reset_logs
  root=$(new_root unsafe)
  write_manifest "$root"
  build "$root" >/dev/null || fail "the fixture image builds"
  printf '%s\n' "$entry" installer/hardware/c.sh >"$root/var/lib/arch/image/deferred-steps"
  status=0
  first_boot "$root" >/dev/null 2>&1 || status=$?
  (( status == 1 )) || fail "the first boot refuses the queue entry $entry with status 1, not a step failure's 75" "status $status"
  [[ ! -e $RUNS && $(head -n 1 "$root/var/lib/arch/image/deferred-steps") == "$entry" ]] ||
    fail "the first boot refuses the queue entry $entry before running anything"
done
pass "the first boot runs only hardware setup leaves from its queue"

reset_logs
root=$(new_root nothing)
output=$(first_boot "$root") || fail "the first-boot hardware setup succeeds with nothing deferred"
[[ -z $output && ! -e $root/var/lib/arch ]] || fail "the first-boot hardware setup does nothing with nothing deferred" "$output"
pass "with nothing deferred the first-boot hardware setup does nothing"

if env -u ARCH_IMAGE_ROOT ARCH_PATH="$fixture" PATH="$base_path" "$ROOT/src/cli/arch-provision-hardware" >/dev/null 2>&1; then
  fail "the first-boot hardware setup refuses a normal user"
fi
pass "the first-boot hardware setup refuses a normal user"

# The service fires on the queue this helper writes and hands the machine to
# owner setup and the login screen only after it.
grep -qx 'ConditionPathExists=|/var/lib/arch/image/deferred-steps' "$unit_source" &&
  grep -qx 'ExecStart=/usr/bin/arch-provision-hardware' "$unit_source" &&
  grep -qx 'Before=arch-provision-owner.service display-manager.service' "$unit_source" &&
  grep -qx 'WantedBy=multi-user.target' "$unit_source" ||
  fail "the first-boot hardware service runs on the queue before owner setup and the login screen"
pass "the first-boot hardware service runs on the queue before owner setup and the login screen"

# --- Bluetooth on the first boot ---------------------------------------------

# The adapter brings up bluetooth.target before the first boot runs the
# Bluetooth leaf, and a target never starts a unit enabled after its start job
# was made, so that boot has to start bluetooth.service itself. Nothing else
# does: an install or a rerun of hardware setup leaves the service as it finds it.
bt_fixture="$test_tmp/arch-bluetooth"
mkdir -p "$bt_fixture/installer/helpers" "$bt_fixture/installer/provisioning" "$bt_fixture/installer/hardware" \
  "$bt_fixture/src/python/installer/hardware" "$bt_fixture/data/installer"
cp "$ROOT/installer/helpers/logging.sh" "$ROOT/installer/helpers/image-target.sh" "$bt_fixture/installer/helpers/"
cp "$unit_source" "$bt_fixture/installer/provisioning/"
cp "$ROOT/src/python/installer/hardware/bluetooth.py" "$bt_fixture/src/python/installer/hardware/"
cp "$ROOT/data/installer/hardware.yml" "$bt_fixture/data/installer/hardware.yml"
cp "$fixture/installer/hardware/c.sh" "$bt_fixture/installer/hardware/"
printf 'run_logged "$ARCH_PATH/src/python/installer/hardware/bluetooth.py"\nrun_logged "$ARCH_INSTALL/hardware/c.sh"\n' >"$bt_fixture/installer/hardware/all.sh"

bt_bin="$test_tmp/bt-bin"
mkdir -p "$bt_bin"
cat >"$bt_bin/systemctl" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$SYSTEMCTL_CALLS"
case $* in
  "start --no-block bluetooth.service") [[ ! -e $BT_START_REFUSED ]] ;;
  *) exit 0 ;;
esac
SH
chmod +x "$bt_bin/systemctl"
export SYSTEMCTL_CALLS="$test_tmp/systemctl-calls" BT_START_REFUSED="$test_tmp/bt-start-refused"
bt_path="$bt_bin:$base_path"

bt_image() {
  local root
  root=$(new_root "bt-$1")
  write_manifest "$root"
  ARCH_IMAGE_ROOT="$root" ARCH_PATH="$bt_fixture" ARCH_INSTALL_LOG_FILE="$root/var/log/arch-install.log" \
    PATH="$bt_path" "$apply_hardware" --defer-provisioning >/dev/null || fail "the Bluetooth fixture image builds"
  printf '%s\n' "$root"
}

bt_first_boot() {
  rm -f "$SYSTEMCTL_CALLS" "$RUNS"
  ARCH_IMAGE_ROOT="$1" ARCH_PATH="$bt_fixture" ARCH_PROC_ROOT="$test_tmp/hw/proc" \
    PATH="$bt_path" "$ROOT/src/cli/arch-provision-hardware" >/dev/null 2>&1
}

started=$'enable bluetooth.service\nstart --no-block bluetooth.service'

reset_logs
rm -f "$BT_START_REFUSED" "$SYSTEMCTL_CALLS"
root=$(bt_image started)
[[ ! -e $SYSTEMCTL_CALLS ]] || fail "an image build touches no Bluetooth unit" "$(cat "$SYSTEMCTL_CALLS")"
bt_first_boot "$root" || fail "the first boot finishes the Bluetooth leaf"
[[ $(<"$SYSTEMCTL_CALLS") == "$started" ]] ||
  fail "the first boot enables Bluetooth and starts it without waiting for the job" "$(<"$SYSTEMCTL_CALLS")"
[[ $(cat "$RUNS") == c && ! -e $root/var/lib/arch/image/deferred-steps ]] ||
  fail "the first boot goes on past the Bluetooth leaf"
pass "the first boot enables Bluetooth and starts it in the same session"

touch "$BT_START_REFUSED"
root=$(bt_image refused)
bt_first_boot "$root" || fail "a refused Bluetooth start does not fail the first boot"
[[ $(<"$SYSTEMCTL_CALLS") == "$started" && $(cat "$RUNS") == c && ! -e $root/var/lib/arch/image/deferred-steps ]] ||
  fail "a refused Bluetooth start leaves the step done and the queue going" "$(<"$SYSTEMCTL_CALLS")"
pass "a refused Bluetooth start does not fail the first boot"
rm -f "$BT_START_REFUSED"

# A later boot that retries the queue is still the machine's own first setup.
root=$(bt_image retry)
mv "$root/var/lib/arch/image/target" "$root/var/lib/arch/image/target.booted"
bt_first_boot "$root" || fail "a retried queue finishes"
[[ $(<"$SYSTEMCTL_CALLS") == "$started" ]] ||
  fail "a retried queue starts Bluetooth like the first run" "$(<"$SYSTEMCTL_CALLS")"
pass "a retried queue starts Bluetooth like the first run"

# Hardware setup outside the first boot, even with the marker inherited.
rm -f "$SYSTEMCTL_CALLS" "$RUNS"
root=$(new_root bt-live)
ARCH_IMAGE_DEFERRED_HARDWARE=1 ARCH_IMAGE_ROOT="$root" ARCH_PATH="$bt_fixture" \
  ARCH_INSTALL_LOG_FILE="$root/var/log/arch-install.log" PATH="$bt_path" "$apply_hardware" --defer-provisioning >/dev/null ||
  fail "hardware setup without a manifest runs the Bluetooth leaf"
[[ $(<"$SYSTEMCTL_CALLS") == "enable bluetooth.service" && $(cat "$RUNS") == c ]] ||
  fail "hardware setup outside the first boot only enables Bluetooth" "$(<"$SYSTEMCTL_CALLS")"
pass "hardware setup outside the first boot only enables Bluetooth, as an install always has"

# --- Root ignores the fixture root ------------------------------------------

# As namespaced root the fixture root in the environment is ignored: the
# fixture image is not built into, and hardware setup runs as on any live system.
if [[ -e /var/lib/arch/image ]]; then
  pass "this machine keeps image state of its own; skipping the root override probe"
elif unshare --user --map-root-user true 2>/dev/null; then
  root_runner=(unshare --user --map-root-user)

  reset_logs
  root=$(new_root root-build)
  write_manifest "$root"
  ARCH_IMAGE_ROOT="$root" ARCH_PATH="$fixture" ARCH_INSTALL_LOG_FILE="$root/var/log/arch-install.log" \
    PATH="$base_path" "${root_runner[@]}" "$ROOT/src/cli/arch-apply-hardware" --defer-provisioning >/dev/null ||
    fail "root runs hardware setup with a fixture root in its environment"
  [[ $(cat "$RUNS") == $'a user= path='"$fixture"$'\nb\nc' && ! -e $root/var/lib/arch/image/deferred-steps ]] ||
    fail "root ignores a fixture manifest named by its environment"

  # Both commands take every path from the helper, which as root answers with
  # the live ones whatever the environment says.
  resolved=$(ARCH_IMAGE_ROOT="$root" "${root_runner[@]}" bash -c \
    'source "$1"; arch_image_init && printf "%s\n" "$arch_image_manifest" "$arch_image_queue" "$arch_image_systemd_dir"' \
    bash "$ROOT/installer/helpers/image-target.sh") || fail "root resolves the image paths"
  [[ $resolved == $'/var/lib/arch/image/target\n/var/lib/arch/image/deferred-steps\n/etc/systemd/system' ]] ||
    fail "root resolves the live image paths whatever its environment names" "$resolved"
  pass "root ignores fixture roots in its environment"
else
  pass "no unprivileged user namespace; skipping the root override probe"
fi
