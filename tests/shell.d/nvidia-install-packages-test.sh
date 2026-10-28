#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
mock_bin="$scratch/bin"
package_log="$scratch/packages"
mkdir -p "$mock_bin"
export PACKAGE_LOG="$package_log"

cat >"$mock_bin/lspci" <<'SH'
#!/bin/bash
printf '%s\n' "3D controller: ${TEST_NVIDIA_DEVICE:-NVIDIA Corporation}"
SH
cat >"$mock_bin/arch-hw-aarch64-n1x" <<'SH'
#!/bin/bash
exit 1
SH
cat >"$mock_bin/arch-hw-x86" <<'SH'
#!/bin/bash
[[ ${TEST_ARCH:-} == x86_64 ]]
SH
cat >"$mock_bin/arch-hw-nvidia-gsp" <<'SH'
#!/bin/bash
[[ ${TEST_DRIVER:-} == gsp ]]
SH
cat >"$mock_bin/arch-hw-nvidia-without-gsp" <<'SH'
#!/bin/bash
[[ ${TEST_DRIVER:-} == legacy ]]
SH
cat >"$mock_bin/arch-pkg-add" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >"$PACKAGE_LOG"
SH
chmod +x "$mock_bin"/*

assert_packages() {
  local description="$1" architecture="$2" driver="$3" expected="$4"
  rm -rf "$scratch/root"
  mkdir -p "$scratch/root"
  : >"$package_log"
  TEST_ARCH="$architecture" TEST_DRIVER="$driver" AP="$ROOT" ARCH_SYSTEM_ROOT="$scratch/root" \
    PATH="$mock_bin:$PATH" python3 -I "$ROOT/src/arch/python/installer/hardware/nvidia.py" >/dev/null ||
    fail "$description" "NVIDIA setup failed"
  local actual
  actual=$(<"$package_log")
  [[ $actual == "$expected" ]] || fail "$description" "expected: $expected; actual: $actual"
  pass "$description"
}

assert_packages "ARM GSP selection uses native packages" aarch64 gsp \
  'nvidia-open-dkms nvidia-utils libva-nvidia-driver'
assert_packages "ARM legacy selection omits x86 multilib" aarch64 legacy \
  'nvidia-580xx-dkms nvidia-580xx-utils'
assert_packages "x86 GSP package selection stays unchanged" x86_64 gsp \
  'nvidia-open-dkms nvidia-utils lib32-nvidia-utils libva-nvidia-driver'
assert_packages "x86 legacy package selection stays unchanged" x86_64 legacy \
  'nvidia-580xx-dkms nvidia-580xx-utils lib32-nvidia-580xx-utils'
