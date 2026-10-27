#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

fix_t2="$ROOT/installer/hardware/apple/fix-t2.sh"
other_packages="$ROOT/installer/arch-other.packages"

grep -Fq 'KERNEL_CMDLINE[default]+=" intel_iommu=on iommu=pt pm_async=off mem_sleep_default=deep"' "$fix_t2" ||
  fail "T2 setup installs the suspend kernel parameters"
! grep -q 'pcie_ports=compat' "$fix_t2" ||
  fail "T2 setup drops the obsolete PCIe compatibility parameter"
(( $(grep -Ec '^\[Fan[12]\]$' "$fix_t2") == 2 )) ||
  fail "T2 setup configures both possible MacBook fans"
(( $(grep -c '^speed_curve=linear$' "$fix_t2") == 2 )) ||
  fail "T2 setup preserves the tuned linear curve for both fans"
! grep -q 'tiny-dfr' "$fix_t2" ||
  fail "T2 setup leaves optional Touch Bar customization uninstalled"
! grep -qx 'tiny-dfr' "$other_packages" ||
  fail "the ISO no longer caches tiny-dfr"
grep -Fq 'apple-bcm-firmware-fetcher' "$fix_t2" ||
  fail "T2 setup installs the firmware fetcher"
grep -Fq 'apple-bcm-firmware-fetcher' "$other_packages" ||
  fail "the default package list installs the firmware fetcher"
pass "fresh T2 setup uses t2bce-compatible suspend, fan, and Touch Bar defaults"
