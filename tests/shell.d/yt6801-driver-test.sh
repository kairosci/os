#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

stub_bin="$test_tmp/bin"
mkdir -p "$stub_bin"
export TEST_STATE="$test_tmp/state"
export TEST_CALLS="$test_tmp/calls"
export TEST_FAULT=""
export TEST_DEVICE="0000:01:00.0"
export TEST_DEVICE_2="0000:02:00.0"
export PATH="$stub_bin:$PATH"

# Model kernel state separately from package files: DKMS removal deletes the
# latter and refreshes depmod, but cannot unload the module already in memory.
cat >"$stub_bin/stub" <<'SH'
#!/bin/bash
set -euo pipefail
command=${0##*/}
printf '%s %s\n' "$command" "$*" >>"$TEST_CALLS"

case "$command" in
  lspci)
    [[ $* == "-Dn -d 1f0a:6801" ]] || exit 90
    [[ $TEST_FAULT != "pci-fail" ]] || exit 1
    cat "$TEST_STATE/devices"
    [[ $TEST_FAULT != "pci-partial" ]] || exit 1
    ;;
  pacman)
    if [[ $* == "-Qq" ]]; then
      query_count=$(<"$TEST_STATE/queries")
      query_count=$((query_count + 1))
      printf '%s\n' "$query_count" >"$TEST_STATE/queries"
      printf '%s\n' linux
      if [[ -e $TEST_STATE/package ]]; then
        printf '%s\n' yt6801-dkms
      fi
      [[ $TEST_FAULT != "query-fail" ]] || exit 1
      if [[ $TEST_FAULT == "helper-query-fail" ]] && (( query_count == 2 )); then
        exit 1
      fi
      if [[ $TEST_FAULT == "final-query-fail" ]] && [[ ! -e $TEST_STATE/package ]]; then
        exit 1
      fi
    elif [[ $* == "-Rns --noconfirm yt6801-dkms" ]]; then
      [[ $TEST_FAULT != "remove-fail" ]] || exit 1
      if [[ $TEST_FAULT != "remove-noop" ]]; then
        rm -f "$TEST_STATE/package" "$TEST_STATE/module-files"
      fi
      if [[ $TEST_FAULT == "remove-reload" ]]; then
        touch "$TEST_STATE/vendor-loaded"
      elif [[ $TEST_FAULT == "remove-unbind" ]]; then
        rm -f "$TEST_STATE/bindings/$TEST_DEVICE"
      fi
      [[ $TEST_FAULT != "remove-interrupt" ]] || exit 1
    else
      exit 90
    fi
    ;;
  lsmod)
    [[ $TEST_FAULT != "modules-fail" ]] || exit 1
    if [[ $TEST_FAULT == "final-modules-fail" && ! -e $TEST_STATE/package ]]; then
      exit 1
    fi
    printf '%s\n' 'Module Size Used by'
    if [[ -e $TEST_STATE/vendor-loaded ]]; then
      printf '%s\n' 'yt6801 65536 0'
    fi
    ;;
  readlink)
    [[ $# == 2 && $1 == "-f" && $2 == /sys/bus/pci/devices/*/driver ]] || exit 90
    device=${2%/driver}
    device=${device##*/}
    [[ $TEST_FAULT != "binding-read-fail" ]] || exit 1
    if [[ -e $TEST_STATE/bindings/$device ]]; then
      printf '/sys/bus/pci/drivers/%s\n' "$(<"$TEST_STATE/bindings/$device")"
    else
      printf '%s\n' "$2"
    fi
    ;;
  modinfo)
    [[ $* == "-F alias dwmac-motorcomm" ]] || exit 90
    [[ $TEST_FAULT != "alias-fail" ]] || exit 1
    if [[ $TEST_FAULT == "alias-wrong" ]]; then
      printf '%s\n' 'pci:v00001F0Ad00006802sv*sd*bc*sc*i*'
    else
      printf '%s\n' 'pci:v00001F0Ad00006801sv*sd*bc*sc*i*'
    fi
    ;;
  modprobe)
    # Real modprobe cannot resolve a module through its deleted lookup entry.
    if [[ $* == "-r yt6801" ]]; then
      [[ -e $TEST_STATE/module-files ]] || exit 1
      exit 90
    fi
    [[ $* == "dwmac-motorcomm" ]] || exit 90
    [[ $TEST_FAULT != "load-fail" ]] || exit 1
    if [[ $TEST_FAULT != "load-noop" ]]; then
      touch "$TEST_STATE/upstream-loaded"
    fi
    [[ $TEST_FAULT != "load-interrupt" ]] || exit 1
    ;;
  rmmod)
    [[ $* == "yt6801" ]] || exit 90
    [[ $TEST_FAULT != "unload-fail" ]] || exit 1
    [[ -e $TEST_STATE/vendor-loaded ]] || exit 1
    if [[ $TEST_FAULT != "unload-noop" ]]; then
      rm "$TEST_STATE/vendor-loaded"
      for binding in "$TEST_STATE/bindings/"*; do
        if [[ -f $binding && $(<"$binding") == "yt6801" ]]; then
          rm "$binding"
        fi
      done
    fi
    [[ $TEST_FAULT != "unload-interrupt" ]] || exit 1
    ;;
  tee)
    [[ $* == "/sys/bus/pci/drivers_probe" ]] || exit 90
    read -r device
    [[ $device == "$TEST_DEVICE" || $device == "$TEST_DEVICE_2" ]] || exit 90
    [[ $TEST_FAULT != "probe-fail" ]] || exit 1
    if [[ $TEST_FAULT != "probe-noop" && -e $TEST_STATE/upstream-loaded && ! -e $TEST_STATE/bindings/$device ]]; then
      if [[ $TEST_FAULT != "second-probe-noop" || $device != "$TEST_DEVICE_2" ]]; then
        printf '%s\n' dwmac-motorcomm >"$TEST_STATE/bindings/$device"
      fi
    fi
    [[ $TEST_FAULT != "probe-interrupt" ]] || exit 1
    ;;
  sudo)
    [[ $TEST_FAULT != "sudo-fail" ]] || exit 1
    case "$*" in
      'modprobe dwmac-motorcomm'|'rmmod yt6801'|'tee /sys/bus/pci/drivers_probe'|'pacman -Rns --noconfirm yt6801-dkms') "$@" ;;
      *) exit 90 ;;
    esac
    ;;
  arch-notification-dismiss) ;;
  *) exit 90 ;;
esac
SH
chmod +x "$stub_bin/stub"
for command in lspci pacman lsmod readlink modinfo modprobe rmmod tee sudo arch-notification-dismiss; do
  ln -s stub "$stub_bin/$command"
done
ln -s "$ROOT/src/arch/commands/arch-pkg-drop" "$stub_bin/arch-pkg-drop"

reset_state() {
  rm -rf "$TEST_STATE"
  mkdir -p "$TEST_STATE/bindings"
  : >"$TEST_CALLS"
  TEST_FAULT=""
  printf '%s\n' 0 >"$TEST_STATE/queries"
  printf '%s 0200: 1f0a:6801\n' "$TEST_DEVICE" >"$TEST_STATE/devices"
  printf '%s\n' yt6801 >"$TEST_STATE/bindings/$TEST_DEVICE"
  touch "$TEST_STATE/package" "$TEST_STATE/module-files" "$TEST_STATE/vendor-loaded"
}

if grep -Fxq 'yt6801-dkms' "$ROOT/installer/arch-other.packages"; then
  fail "default package list still installs yt6801-dkms"
fi
pass "the default package list no longer installs the vendor driver"
