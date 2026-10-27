#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

surface_setup="$ROOT/src/python/installer/hardware/surface_firmware.py"
keyboard_setup="$ROOT/installer/hardware/fix-surface-keyboard.sh"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT

bash -n "$keyboard_setup" || fail "Surface keyboard script has valid syntax"

mkinitcpio_dir="$scratch/mkinitcpio.conf.d"
module_list="$mkinitcpio_dir/surface_device_modules.conf"

# A third argument is what the mocked lsmod prints; without one, no module is
# detected and the script writes nothing.
run_surface_setup() (
  machine=$1
  script=$2
  loaded_modules=${3:-}
  if [[ $script == *.py ]]; then
    PATH="$scratch/bin:$PATH" ARCH_PATH="$ROOT" ARCH_TEST_MACHINE="$machine" \
      ARCH_TEST_PACKAGES="$scratch/packages" python3 -I "$script"
  else
    arch-hw-surface() { return 0; }
    arch-hw-x86() { [[ $machine == "x86_64" ]]; }
    arch-pkg-add() { printf '%s\n' "$*" >>"$scratch/packages"; }
    lsmod() {
      printf 'lsmod\n' >>"$scratch/probes"
      printf '%s\n' "$loaded_modules"
    }
    # The keyboard script reads the DMI product name from sysfs, which ARM
    # machines and containers may not have. Answer that read as an Intel Surface
    # so the test does not depend on the host's firmware tables.
    cat() {
      if [[ $* == "/sys/class/dmi/id/product_name" ]]; then
        printf 'Surface Laptop 3\n'
      else
        command cat "$@"
      fi
    }
    ARCH_SURFACE_MKINITCPIO_DIR="$mkinitcpio_dir" source "$script"
  fi
)
mkdir -p "$scratch/bin"
cat >"$scratch/bin/arch-hw-surface" <<'SH'
#!/bin/bash
exit "${ARCH_TEST_SURFACE_STATUS:-0}"
SH
cat >"$scratch/bin/arch-hw-x86" <<'SH'
#!/bin/bash
[[ ${ARCH_TEST_MACHINE:-} == "x86_64" ]]
SH
cat >"$scratch/bin/arch-pkg-add" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$ARCH_TEST_PACKAGES"
exit "${ARCH_TEST_PKG_STATUS:-0}"
SH
cat >"$scratch/bin/arch-hw-device-match" <<'SH'
#!/bin/bash
gate=${0##*/}
case ",${ARCH_TEST_MATCHED:-}," in
  *,"$gate",*) exit 0 ;;
  *) exit 1 ;;
esac
SH
chmod +x "$scratch/bin/arch-hw-surface" "$scratch/bin/arch-hw-x86" "$scratch/bin/arch-pkg-add" "$scratch/bin/arch-hw-device-match"
for gate in arch-hw-asus-rog arch-hw-framework16 arch-hw-dell-xps-haptic-touchpad; do
  ln -s arch-hw-device-match "$scratch/bin/$gate"
done

run_package_gates() (
  matched=$1
  status=${2:-0}
  PATH="$scratch/bin:$PATH" ARCH_PATH="$ROOT" ARCH_TEST_MATCHED="$matched" \
    ARCH_TEST_PKG_STATUS="$status" ARCH_TEST_PACKAGES="$scratch/packages" \
    python3 -I "$ROOT/src/python/installer/hardware/package_gates.py"
)

: >"$scratch/packages"
run_package_gates "arch-hw-framework16,arch-hw-dell-xps-haptic-touchpad"
[[ $(cat "$scratch/packages") == $'qmk-hid\ndell-xps-touchpad-haptics' ]] ||
  fail "hardware package gates install only packages for matching devices"
: >"$scratch/packages"
if run_package_gates "arch-hw-framework16,arch-hw-dell-xps-haptic-touchpad" 6; then
  fail "package gate reports a package installation failure"
fi
[[ $(cat "$scratch/packages") == $'qmk-hid\ndell-xps-touchpad-haptics' ]] ||
  fail "a failed hardware package install does not skip later gates"
pass "hardware package gates preserve matching, order, and failure behavior"

rm -f "$scratch/packages" "$scratch/probes"
run_surface_setup aarch64 "$surface_setup" >/dev/null
[[ ! -e $scratch/packages ]] ||
  fail "Surface setup skips Marvell firmware on Snapdragon Surfaces"

# What lsmod reports on a Surface Pro 11, where the Intel module list would break mkinitcpio.
run_surface_setup aarch64 "$keyboard_setup" "pinctrl_sm8550_lpass_lpi 12288 1" >/dev/null
[[ ! -e $scratch/probes && ! -e $module_list ]] ||
  fail "Surface keyboard setup skips Intel modules on Snapdragon Surfaces"

run_surface_setup x86_64 "$surface_setup" >/dev/null
[[ $(<"$scratch/packages") == "linux-firmware-marvell" ]] ||
  fail "Surface setup installs Marvell firmware on Intel Surfaces"

run_surface_setup x86_64 "$keyboard_setup" >/dev/null
[[ -e $scratch/probes && ! -e $module_list ]] ||
  fail "Surface keyboard setup probes modules on Intel Surfaces and writes nothing without a pinctrl module"

run_surface_setup x86_64 "$keyboard_setup" "pinctrl_tigerlake 32768 0" >/dev/null
[[ -f $module_list ]] ||
  fail "Surface keyboard setup writes the initramfs module list on Intel Surfaces"
[[ $(<"$module_list") == "MODULES=(pinctrl_tigerlake surface_aggregator surface_aggregator_registry surface_aggregator_hub surface_hid_core surface_hid surface_kbd intel_lpss_pci 8250_dw)" ]] ||
  fail "Surface keyboard setup lists the detected pinctrl module ahead of the Surface and Intel LPSS modules" "$(<"$module_list")"

pass "Surface hardware setup applies Intel fixes only on x86_64"
