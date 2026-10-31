#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/bin"
cat >"$scratch/bin/archctl" <<'SH'
#!/bin/bash
[[ ${1:-} == hw && ${2:-} == intel && ${3:-} == sof && $# == 3 ]] || exit 2
case ",${ARCH_TEST_MATCHED:-}," in
  *,arch-hw-intel-sof,*) exit 0 ;;
  *) exit 1 ;;
esac
SH
cat >"$scratch/bin/arch-pkg-add" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$ARCH_TEST_PACKAGES"
exit "${ARCH_TEST_PKG_STATUS:-0}"
SH
chmod +x "$scratch/bin/archctl" "$scratch/bin/arch-pkg-add"
run_package_gates() (
  matched=$1
  status=${2:-0}
  PATH="$scratch/bin:$PATH" AP="$ROOT" ARCH_TEST_MATCHED="$matched" \
    ARCH_TEST_PKG_STATUS="$status" ARCH_TEST_PACKAGES="$scratch/packages" \
    python3 -I "$ROOT/src/arch/python/installer/hardware/package_gates.py"
)
: >"$scratch/packages"
run_package_gates "arch-hw-intel-sof"
[[ $(cat "$scratch/packages") == "sof-firmware" ]] || fail "Intel SOF devices receive their firmware package"
: >"$scratch/packages"
if run_package_gates "arch-hw-intel-sof" 6; then
  fail "package gates report package installation failures"
fi
[[ $(cat "$scratch/packages") == "sof-firmware" ]] || fail "failed package installs are attempted exactly once"
pass "generic hardware package gates preserve matching and failure behavior"
