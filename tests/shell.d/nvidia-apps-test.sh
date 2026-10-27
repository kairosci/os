#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/base-test.sh"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
calls="$scratch/calls"
mock_bin="$scratch/bin"
mkdir -p "$mock_bin"
export mock_bin

cat >"$mock_bin/arch-pkg-present" <<'SH'
#!/bin/bash
[[ " ${INSTALLED_PACKAGES:-} " == *" $1 "* ]]
SH
cat >"$mock_bin/nvidia-ctk" <<'SH'
#!/bin/bash
printf 'nvidia-ctk %s\n' "$*" >>"$CALLS"
[[ ${SETUP_FAILURE:-} != nvidia-ctk ]]
SH
cat >"$mock_bin/systemctl" <<'SH'
#!/bin/bash
printf 'systemctl %s\n' "$*" >>"$CALLS"
[[ ${SETUP_FAILURE:-} != "$1" ]]
SH
chmod +x "$mock_bin"/*

run_setup() (
  installed=$1
  failure=${2:-}
  export ARCH_PATH="$ROOT"
  export CALLS="$calls"
  export INSTALLED_PACKAGES="$installed"
  export SETUP_FAILURE="$failure"
  export ARCH_IMAGE_DEFERRED_HARDWARE=${3:-}
  PATH="$mock_bin:$PATH" python3 -I "$ROOT/src/python/installer/hardware/nvidia_apps.py"
)

grep -Fq 'src/python/installer/hardware/nvidia_apps.py' "$ROOT/data/installer/hardware-setup.yml" ||
  fail "hardware setup runs the NVIDIA apps module"

for deferred in "" 0 1; do
  for mask in {0..7}; do
    packages=()
    expected=()
    if (( mask & 1 )); then
      packages+=(nvidia-ai-workbench)
      expected+=('nvidia-ctk runtime configure --runtime=docker')
    fi
    if (( mask & 2 )); then
      packages+=(dgx-dashboard)
      expected+=('systemctl enable dgx-dashboard.service')
      if [[ $deferred == "1" ]]; then
        expected+=('systemctl start --no-block dgx-dashboard.service')
      fi
    fi
    if (( mask & 4 )); then
      packages+=(ollama)
    fi
    : > "$calls"
    run_setup "${packages[*]}" "" "$deferred"
    actual=$(cat "$calls")
    wanted=$(printf '%s\n' "${expected[@]}")
    [[ $actual == "$wanted" ]] || fail "installed applications receive only their own setup" "$actual"
  done
done
pass "all package combinations start Dashboard only during deferred first-boot setup"
pass "hardware setup leaves optional Ollama service management alone"

export ROOT calls
export -f run_setup
for deferred in "" 1; do
  for failure in nvidia-ctk enable; do
    : > "$calls"
    # A separate shell preserves errexit while the caller checks the result.
    if bash -euo pipefail -c 'run_setup "nvidia-ai-workbench dgx-dashboard ollama" "$1" "$2"' bash "$failure" "$deferred"; then
      fail "failed $failure setup is propagated"
    fi
  done
done
pass "runtime configuration and service-enable failures stop setup"

: > "$calls"
bash -euo pipefail -c 'run_setup "dgx-dashboard" start 1'
[[ $(<"$calls") == $'systemctl enable dgx-dashboard.service\nsystemctl start --no-block dgx-dashboard.service' ]] ||
  fail "a refused Dashboard start is attempted without failing deferred setup" "$(<"$calls")"
pass "a refused Dashboard start does not fail deferred setup"
