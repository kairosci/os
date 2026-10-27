#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

firmware_setup="$ROOT/src/python/installer/hardware/qualcomm/firmware.py"
dtb_setup="$ROOT/src/python/installer/hardware/qualcomm/dtb_uki.py"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT

mock_bin="$scratch/mock-bin"
mkdir -p "$mock_bin"
cat >"$mock_bin/arch-hw-aarch64-qualcomm" <<'COMMAND'
#!/bin/bash
if [[ -n ${ARCH_PROC_ROOT:-} ]]; then
  exec "$ROOT/src/commands/arch-hw-aarch64-qualcomm" "$@"
fi
exit 0
COMMAND
cat >"$mock_bin/arch-pkg-add" <<'COMMAND'
#!/bin/bash
exit 0
COMMAND
cat >"$mock_bin/qcom-firmware-extract" <<'COMMAND'
#!/bin/bash
if [[ $1 == "--list-missing" ]]; then
  printf '%s\n' "${ARCH_TEST_MISSING:-}"
  exit "${ARCH_TEST_INSPECTION_STATUS:-0}"
fi
exit "${ARCH_TEST_INSTALL_STATUS:-0}"
COMMAND
cat >"$mock_bin/findmnt" <<'COMMAND'
#!/bin/bash
[[ $* == "-no SOURCE --nofsroot /" ]] || exit 2
printf '%s\n' "${ARCH_TEST_ROOT_SOURCE:-}"
COMMAND
cat >"$mock_bin/lsblk" <<'COMMAND'
#!/bin/bash
[[ ${!#} == /dev/mapper/root ]] || exit 2
printf '%s\n' "${ARCH_TEST_ROOT_TRANSPORT:-}"
COMMAND
chmod +x "$mock_bin"/*

run_firmware_setup() (
  ARCH_PATH="$ROOT" \
    ARCH_QUALCOMM_MODPROBE_DIR="$scratch/modprobe.d" \
    PATH="$mock_bin:$PATH" \
    python3 -I "$firmware_setup"
)

export ARCH_TEST_ROOT_SOURCE=/dev/mapper/root ARCH_TEST_ROOT_TRANSPORT=usb
run_firmware_setup

[[ -f $scratch/modprobe.d/qualcomm-adsp-nofw.conf ]] ||
  fail "Snapdragon firmware setup protects a USB-backed root disk"

export ARCH_TEST_ROOT_TRANSPORT=nvme ARCH_TEST_INSPECTION_STATUS=1
run_firmware_setup
[[ -f $scratch/modprobe.d/qualcomm-adsp-nofw.conf ]] ||
  fail "Snapdragon setup keeps DSPs disabled when firmware inspection fails"
export ARCH_TEST_INSPECTION_STATUS=0
run_firmware_setup
[[ ! -f $scratch/modprobe.d/qualcomm-adsp-nofw.conf ]] ||
  fail "Snapdragon setup enables DSPs after firmware is verified on an internal root"

mkdir -p "$scratch/dtbs"
: >"$scratch/dtbs/x1e80100-test.dtb"
: >"$scratch/dtbs/x1e80100-test-el2.dtb"
cat >"$scratch/uki.conf" <<'CONF'
[UKI]
SecureBootPrivateKey=/secure/db.key
PCRPrivateKey=/secure/pcr.key
CONF

run_dtb_setup() (
  ARCH_PATH="$ROOT" \
    ARCH_QUALCOMM_DTB_DIR="$scratch/dtbs" \
    ARCH_QUALCOMM_UKI_CONFIG="$scratch/uki.conf" \
    PATH="$mock_bin:$PATH" \
    python3 -I "$dtb_setup"
)

run_dtb_setup
first_uki_config=$(<"$scratch/uki.conf")
run_dtb_setup
[[ $(<"$scratch/uki.conf") == "$first_uki_config" ]] ||
  fail "Snapdragon DTB setup is idempotent"

grep -Fq 'SecureBootPrivateKey=/secure/db.key' "$scratch/uki.conf" ||
  fail "Snapdragon DTB setup preserves Secure Boot settings"
grep -Fq 'PCRPrivateKey=/secure/pcr.key' "$scratch/uki.conf" ||
  fail "Snapdragon DTB setup preserves PCR settings"
[[ $(grep -Fc '# BEGIN ARCH QUALCOMM DEVICE TREES' "$scratch/uki.conf") == 1 ]] ||
  fail "Snapdragon DTB setup keeps one managed UKI block"
grep -Fq "DeviceTreeAuto=$scratch/dtbs/x1e80100-test.dtb" "$scratch/uki.conf" ||
  fail "Snapdragon DTB setup lists the matching device tree"
if grep -Fq 'x1e80100-test-el2.dtb' "$scratch/uki.conf"; then
  fail "Snapdragon DTB setup excludes EL2-only device trees"
fi

# An image's first boot rebuilds once after its last step and does not watch
# uki.conf, so a changed list asks for that rebuild and an unchanged one does not.
request="$scratch/boot-rebuild"
: >"$scratch/dtbs/x1e80100-added.dtb"
(export ARCH_IMAGE_BOOT_REBUILD="$request" && run_dtb_setup)
[[ -e $request ]] ||
  fail "a changed device tree list asks an image's first boot for the rebuild"
rm -f "$request"
(export ARCH_IMAGE_BOOT_REBUILD="$request" && run_dtb_setup)
[[ ! -e $request ]] ||
  fail "an unchanged device tree list asks for no rebuild"

# os's own kernel keeps its device trees under its package name. They come
# before Arch Linux ARM's, so the trees match the kernel that boots.
mkdir -p "$scratch/dtbroot/qcom" "$scratch/dtbroot/linux/qcom"
: >"$scratch/dtbroot/qcom/x1e80100-stock.dtb"
: >"$scratch/dtbroot/linux/qcom/x1e80100-own.dtb"
run_dtb_root_setup() (
  ARCH_PATH="$ROOT" \
    ARCH_QUALCOMM_DTB_ROOT="$scratch/dtbroot" \
    ARCH_QUALCOMM_UKI_CONFIG="$scratch/uki-root.conf" \
    PATH="$mock_bin:$PATH" \
    python3 -I "$dtb_setup"
)
run_dtb_root_setup
grep -Fq "DeviceTreeAuto=$scratch/dtbroot/linux/qcom/x1e80100-own.dtb" "$scratch/uki-root.conf" ||
  fail "Snapdragon DTB setup takes the device trees of os's own kernel first"
rm -r "$scratch/dtbroot/linux"
run_dtb_root_setup
grep -Fq "DeviceTreeAuto=$scratch/dtbroot/qcom/x1e80100-stock.dtb" "$scratch/uki-root.conf" ||
  fail "Snapdragon DTB setup falls back to Arch Linux ARM's device trees"

pass "Snapdragon setup tolerates missing firmware and preserves UKI settings"

defaults=$(ARCH_PATH="$ROOT" "$ROOT/src/commands/arch-pkg-defaults" aarch64-qualcomm)
for package in linux-firmware-qcom qcom-firmware-extract systemd-ukify vulkan-freedreno; do
  grep -qx "$package" <<<"$defaults" ||
    fail "the Snapdragon package set has $package for offline setup"
done
pass "the Snapdragon package set has every package its setup installs"

# The leaves ask arch-hw-aarch64-qualcomm, so run them under the real
# detector: a Snapdragon device tree gets the setup and no other platform does.
require_platform_fixtures "Snapdragon setup under the real detector"

kernel_params_setup="$ROOT/src/python/installer/hardware/qualcomm/kernel_params.py"
initramfs_setup="$ROOT/src/python/installer/hardware/qualcomm/initramfs.py"

run_leaves_on() (
  platform=$1
  out="$scratch/on/$platform"
  mkdir -p "$out"
  fake_platform "$scratch/platforms/$platform" "$platform"
  export ARCH_PROC_ROOT="$scratch/platforms/$platform/proc"
  export PATH="$scratch/platforms/$platform/bin:$mock_bin:$ROOT/src/commands:$PATH"

  arch-pkg-add() { :; }
  qcom-firmware-extract() { [[ $1 != "--list-missing" ]]; }
  findmnt() { printf '/dev/mapper/root\n'; }
  lsblk() { printf 'nvme\n'; }

  ARCH_QUALCOMM_MODPROBE_DIR="$out/modprobe.d"
  ARCH_QUALCOMM_DTB_DIR="$scratch/dtbs"
  ARCH_QUALCOMM_UKI_CONFIG="$out/uki.conf"
  ARCH_QUALCOMM_MKINITCPIO_DIR="$out/mkinitcpio.conf.d"
  ARCH_PATH="$ROOT" ARCH_QUALCOMM_MODPROBE_DIR="$out/modprobe.d" \
    ARCH_TEST_ROOT_SOURCE=/dev/mapper/root ARCH_TEST_ROOT_TRANSPORT=nvme \
    ARCH_TEST_INSPECTION_STATUS=1 PATH="$scratch/platforms/$platform/bin:$mock_bin:$ROOT/src/commands:$PATH" \
    python3 -I "$firmware_setup"
  ARCH_PATH="$ROOT" ARCH_QUALCOMM_DTB_DIR="$scratch/dtbs" \
    ARCH_QUALCOMM_UKI_CONFIG="$out/uki.conf" \
    PATH="$scratch/platforms/$platform/bin:$mock_bin:$ROOT/src/commands:$PATH" \
    python3 -I "$dtb_setup"
  ARCH_PATH="$ROOT" ARCH_QUALCOMM_KERNEL_PARAMS_FILE="$out/limine-entry-tool.d/qualcomm-snapdragon.conf" \
    python3 -I "$kernel_params_setup"
  ARCH_PATH="$ROOT" ARCH_QUALCOMM_MKINITCPIO_DIR="$out/mkinitcpio.conf.d" \
    python3 -I "$initramfs_setup"
)

run_leaves_on aarch64-qualcomm
snapdragon="$scratch/on/aarch64-qualcomm"
[[ -f $snapdragon/modprobe.d/qualcomm-adsp-nofw.conf ]] ||
  fail "a Snapdragon device tree gets the firmware setup"
grep -Fq "DeviceTreeAuto=" "$snapdragon/uki.conf" ||
  fail "a Snapdragon device tree gets the device tree list"
(
  declare -A KERNEL_CMDLINE=([default]="quiet splash")
  source "$snapdragon/limine-entry-tool.d/qualcomm-snapdragon.conf"
  for parameter in clk_ignore_unused pd_ignore_unused arm64.nopauth systemd.tpm2_wait=0 iommu.passthrough=0; do
    [[ " ${KERNEL_CMDLINE[default]} " == *" $parameter "* ]] ||
      fail "a Snapdragon device tree boots with $parameter"
  done
  [[ ${KERNEL_CMDLINE[default]} == "quiet splash "* ]] ||
    fail "Snapdragon setup preserves the existing boot parameters"
)

(
  # A kernel that builds the X1 platform drivers as modules gets them named for
  # the initramfs, each one optional so another kernel's image still builds.
  MODULES=(first)
  source "$snapdragon/mkinitcpio.conf.d/qualcomm-platform.conf"
  [[ ${MODULES[0]} == first ]] ||
    fail "Snapdragon setup preserves the initramfs modules already named"
  for module in pinctrl-x1e80100 qnoc-x1e80100 spmi-pmic-arb i2c-qcom-geni; do
    [[ " ${MODULES[*]} " == *" $module? "* ]] ||
      fail "a Snapdragon device tree gets $module in its initramfs"
  done
  for module in "${MODULES[@]:1}"; do
    [[ $module == *\? ]] ||
      fail "every Snapdragon platform module is optional ($module)"
  done
)

for platform in aarch64 aarch64-apple x86; do
  run_leaves_on "$platform"
  for written in modprobe.d uki.conf limine-entry-tool.d mkinitcpio.conf.d; do
    [[ ! -e $scratch/on/$platform/$written ]] ||
      fail "$platform gets no Snapdragon setup ($written)"
  done
done
pass "Snapdragon setup follows the real platform detector"
