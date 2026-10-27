#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

setup="$ROOT/src/python/installer/hardware/nvidia/dgx_spark_boot.py"
hardware_setup="$ROOT/data/installer/hardware-setup.yml"
direct_boot="$ROOT/src/cli/arch-boot-direct"
config="$ROOT/data/installer/hardware/nvidia/dgx-spark-boot.yml"
config_name=zz-arch-dgx-spark.conf

scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/bin"

bash -n "$direct_boot" || fail "Direct Boot check has valid syntax"

grep -q 'src/python/installer/hardware/nvidia/dgx_spark_boot.py' "$hardware_setup" ||
  fail "the DGX Spark boot setting runs during hardware setup"
grep -q 'arch-boot-direct' "$config" ||
  fail "hardware setup asks the Direct Boot helper before writing the UKI setting"
pass "the DGX Spark boot setting runs during hardware setup"

# The real GB10 predicate reads fixture machines, which root never does.
require_platform_fixtures "the DGX Spark boot setting"

# An aarch64 machine with a DMI product name, and the GB10's GPU or none.
machine() {
  local dir="$scratch/hw/$1"
  mkdir -p "$dir/proc" "$dir/sys/bus/pci/devices" "$dir/bin" "$dir/dmi"
  printf '%s\n' "$2" >"$dir/dmi/product_name"
  if [[ -n ${3:-} ]]; then
    mkdir -p "$dir/sys/bus/pci/devices/000f:01:00.0"
    printf '0x10de\n' >"$dir/sys/bus/pci/devices/000f:01:00.0/vendor"
    printf '%s\n' "$3" >"$dir/sys/bus/pci/devices/000f:01:00.0/device"
  fi
  printf '#!/bin/bash\n[[ ${1:-} == -m ]] && { echo aarch64; exit 0; }\nexec /usr/bin/uname "$@"\n' >"$dir/bin/uname"
  # arch-hw-match reads the fixed /sys/class/dmi/id; read the fixture's instead.
  printf '#!/bin/bash\ngrep -qi -- "$1" "%s/dmi/product_name"\n' "$dir" >"$dir/bin/arch-hw-match"
  chmod +x "$dir/bin/uname" "$dir/bin/arch-hw-match"
}
machine spark NVIDIA_DGX_Spark 0x2e12
machine gx10 GX10 0x2e12
machine other "XPS 13 9350"

cat >"$scratch/bin/sudo" <<'SH'
#!/bin/bash
printf 'sudo %s\n' "$*" >>"$CALL_LOG"
[[ ${TEST_SUDO_STATUS:-0} == 0 ]] || exit "$TEST_SUDO_STATUS"
[[ $1 != "${TEST_SUDO_FAIL_COMMAND:-}" ]] || exit 1
exec "$@"
SH
cat >"$scratch/bin/limine-mkinitcpio" <<'SH'
#!/bin/bash
printf 'limine-mkinitcpio %s\n' "$*" >>"$CALL_LOG"
exit "${TEST_MKINITCPIO_STATUS:-0}"
SH
cat >"$scratch/bin/efibootmgr" <<'SH'
#!/bin/bash
printf 'efibootmgr\n' >>"$CALL_LOG"
[[ ${TEST_EFIBOOTMGR_STATUS:-0} == 0 ]] || exit "$TEST_EFIBOOTMGR_STATUS"
if [[ -n ${TEST_EFI_FAIL_AFTER:-} ]]; then
  n=$(cat "$TEST_EFI_CALLS_FILE")
  printf '%s\n' $((n + 1)) >"$TEST_EFI_CALLS_FILE"
  if (( n >= TEST_EFI_FAIL_AFTER )); then
    exit 1
  fi
fi
printf '%b\n' "${TEST_EFI_ENTRIES:-Boot0001* Limine\tHD(1,GPT,1-2,0x800,0x400000)/\\\\EFI\\\\limine\\\\limine_aa64.efi}"
SH
chmod +x "$scratch/bin"/*

export CALL_LOG="$scratch/calls.log"
run() {
  local machine=$1 state=$2
  shift 2
  : >"$CALL_LOG"
  PATH="$scratch/hw/$machine/bin:$scratch/bin:$ROOT/src/cli:$PATH" ARCH_PATH="$ROOT" \
    ARCH_PROC_ROOT="$scratch/hw/$machine/proc" ARCH_SYS_ROOT="$scratch/hw/$machine/sys" \
    ARCH_LIMINE_CONFIG_DIR="$state/limine-entry-tool.d" \
    ARCH_DGX_SPARK_BOOT_MARKER="$state/marker" "$@"
}

run spark "$scratch/spark" python3 -I "$setup"
config="$scratch/spark/limine-entry-tool.d/$config_name"
grep -Fxqs "ENABLE_UKI=no" "$config" || fail "the DGX Spark boots without a UKI"
before=$(sha256sum "$config")
run spark "$scratch/spark" python3 -I "$setup"
[[ $(sha256sum "$config") == "$before" ]] || fail "rerunning the setting leaves it unchanged"
for machine in gx10 other; do
  run "$machine" "$scratch/$machine" python3 -I "$setup"
  [[ ! -e $scratch/$machine ]] || fail "the $machine machine keeps its UKI"
done
pass "the DGX Spark setting turns off the UKI and leaves other GB10s and other machines alone"

# limine-entry-tool reads its drop-ins in glob order, so the last ENABLE_UKI wins.
# The setting must follow every shipped drop-in that sets ENABLE_UKI, including
# arch-uki.conf, in any locale the boot tools might run under.
ordering="$scratch/ordering"
mkdir -p "$ordering"
cp "$ROOT"/etc/limine-entry-tool.d/*.conf "$ordering/"
cp "$config" "$ordering/"
grep -lq '^ENABLE_UKI=yes' "$ordering"/*.conf || fail "a shipped drop-in turns the UKI on"
for locale in C C.UTF-8 en_US.UTF-8; do
  effective=$(LC_ALL=$locale bash -c '
    value=
    for file in "$1"/*.conf; do
      line=$(grep "^ENABLE_UKI=" "$file" | tail -n 1) || continue
      value=${line#ENABLE_UKI=}
    done
    echo "$value"' -- "$ordering" 2>/dev/null)
  [[ $effective == "no" ]] || fail "the DGX Spark setting overrides the shipped UKI setting in the $locale locale"
done
pass "the DGX Spark setting sorts after the shipped UKI setting"
