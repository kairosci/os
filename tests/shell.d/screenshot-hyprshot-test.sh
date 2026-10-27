#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

grep -qxF hyprshot "$ROOT/installer/arch-base.packages" || fail "fresh installs include the Arch screenshot utility"
grep -q "^replaces=('omasnap')$" "$ROOT/packages/arch/PKGBUILD" || fail "the runtime package replaces the retired screenshot package"
! grep -qxF omasnap "$ROOT/installer/arch-base.packages" || fail "fresh installs do not include the retired screenshot package"
pass "fresh installs use the repository screenshot utility and replace the retired package"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

stub_bin="$test_tmp/bin"
mkdir -p "$stub_bin"
cat >"$stub_bin/hyprshot" <<'SH'
#!/bin/bash
printf '%s\n' "${HYPRSHOT_DIR:-}" "$*" >"$HYPRSHOT_TEST_LOG"
SH
chmod +x "$stub_bin/hyprshot"

capture_log="$test_tmp/capture.log"
HYPRSHOT_TEST_LOG="$capture_log" PATH="$stub_bin:$PATH" \
  "$ROOT/src/commands/arch-capture-screenshot"
[[ $(sed -n '2p' "$capture_log") == '--mode region' ]] || fail "the screenshot command defaults to region selection"

HYPRSHOT_TEST_LOG="$capture_log" ARCH_SCREENSHOT_DIR="$test_tmp/screenshots" PATH="$stub_bin:$PATH" \
  "$ROOT/src/commands/arch-capture-screenshot" windows copy
[[ $(sed -n '1p' "$capture_log") == "$test_tmp/screenshots" ]] || fail "the configured screenshot directory reaches Hyprshot"
[[ $(sed -n '2p' "$capture_log") == '--mode window --clipboard-only' ]] || fail "window and clipboard modes map to Hyprshot"

HYPRSHOT_TEST_LOG="$capture_log" PATH="$stub_bin:$PATH" \
  "$ROOT/src/commands/arch-capture-screenshot" fullscreen save
[[ $(sed -n '2p' "$capture_log") == '--mode output' ]] || fail "fullscreen maps to output capture and save keeps the default file output"

HYPRSHOT_TEST_LOG="$capture_log" PATH="$stub_bin:$PATH" \
  "$ROOT/src/commands/arch-capture-screenshot" region
[[ $(sed -n '2p' "$capture_log") == '--mode region' ]] || fail "region maps to Hyprshot"

pass "the screenshot command maps its supported modes and output options"
