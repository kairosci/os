#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

mock_bin="$test_tmp/bin"
test_home="$test_tmp/home"
mkdir -p "$mock_bin" "$test_home/.local/share/applications"
# Keep the launcher away from the running browser's singleton socket, which it
# would otherwise hand these test URLs to.
export XDG_CONFIG_HOME="$test_home/.config" XDG_DATA_HOME="$test_home/.local/share"

cat >"$test_home/.local/share/applications/chromium.desktop" <<'EOF'
[Desktop Entry]
Exec=chromium %U
EOF

cat >"$mock_bin/xdg-settings" <<'SH'
#!/bin/bash
[[ -z ${BROWSER:-} ]] || printf '%s\n' "$BROWSER" >"$ARCH_TEST_XDG_SETTINGS_BROWSER"
[[ ${ARCH_TEST_XDG_SETTINGS_EMPTY:-0} == "1" ]] || echo chromium.desktop
SH
cat >"$mock_bin/xdg-mime" <<'SH'
#!/bin/bash
if [[ $* == "query default x-scheme-handler/https" ]]; then
  echo chromium.desktop
fi
SH
cat >"$mock_bin/chromium" <<'SH'
#!/bin/bash
exit 0
SH
cat >"$mock_bin/systemd-run" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >"$ARCH_TEST_BROWSER_LAUNCH"
SH
cat >"$mock_bin/arch-hyprland-focus-app" <<'SH'
#!/bin/bash
printf '%s\n' "$1" >"$ARCH_TEST_BROWSER_FOCUS"
SH
chmod +x "$mock_bin"/*

launch_log="$test_tmp/launch"
focus_log="$test_tmp/focus"
xdg_settings_browser="$test_tmp/xdg-settings-browser"
HOME="$test_home" PATH="$mock_bin:$PATH" HYPRLAND_INSTANCE_SIGNATURE=test \
  ARCH_TEST_BROWSER_LAUNCH="$launch_log" ARCH_TEST_BROWSER_FOCUS="$focus_log" \
  bash "$ROOT/src/arch/commands/arch-launch-browser"

[[ ! -e $focus_log ]] || fail "browser launcher leaves a new window on the current workspace"

HOME="$test_home" PATH="$mock_bin:$PATH" HYPRLAND_INSTANCE_SIGNATURE=test \
  ARCH_TEST_BROWSER_LAUNCH="$launch_log" ARCH_TEST_BROWSER_FOCUS="$focus_log" \
  bash "$ROOT/src/arch/commands/arch-launch-browser" --private

[[ ! -e $focus_log ]] || fail "private browser launcher leaves a new window on the current workspace"

HOME="$test_home" PATH="$mock_bin:$PATH" HYPRLAND_INSTANCE_SIGNATURE=test \
  ARCH_TEST_BROWSER_LAUNCH="$launch_log" ARCH_TEST_BROWSER_FOCUS="$focus_log" \
  bash "$ROOT/src/arch/commands/arch-launch-browser" "https://example.tests/authorize"

grep -F 'https://example.tests/authorize' "$launch_log" >/dev/null || fail "browser launcher passes through the URL"
grep -Fx '^chromium.*$' "$focus_log" >/dev/null || fail "browser launcher focuses the default browser window"

rm -f "$focus_log" "$xdg_settings_browser"

HOME="$test_home" PATH="$mock_bin:$PATH" HYPRLAND_INSTANCE_SIGNATURE=test \
  BROWSER=arch-launch-browser ARCH_TEST_XDG_SETTINGS_EMPTY=1 \
  ARCH_TEST_BROWSER_LAUNCH="$launch_log" ARCH_TEST_BROWSER_FOCUS="$focus_log" \
  ARCH_TEST_XDG_SETTINGS_BROWSER="$xdg_settings_browser" \
  bash "$ROOT/src/arch/commands/arch-launch-browser" "https://example.tests/fallback"

grep -F 'https://example.tests/fallback' "$launch_log" >/dev/null ||
  fail "browser launcher falls back to the HTTPS handler when xdg-settings is empty"
[[ ! -e $xdg_settings_browser ]] ||
  fail "browser launcher unsets BROWSER before reading xdg-settings"
grep -Fx '^chromium.*$' "$focus_log" >/dev/null ||
  fail "browser launcher focuses the browser resolved from the HTTPS handler"

pass "browser launcher follows opened links to the browser workspace"

rm -f "$launch_log"
cat >"$mock_bin/arch-cmd-browser-handoff" <<'SH'
#!/bin/bash
[[ $1 == "chromium" && $2 == "https://example.tests/running" ]]
SH
chmod +x "$mock_bin/arch-cmd-browser-handoff"

HOME="$test_home" PATH="$mock_bin:$PATH" ARCH_TEST_BROWSER_LAUNCH="$launch_log" \
  ARCH_TEST_BROWSER_FOCUS="$focus_log" bash "$ROOT/src/arch/commands/arch-launch-browser" "https://example.tests/running"

[[ ! -e $launch_log ]] || fail "browser launcher starts no browser when the running one takes the URL"
pass "browser launcher hands a URL to the running browser"

rm -f "$mock_bin/arch-cmd-browser-handoff" "$launch_log"
help_log="$test_tmp/help"
cat >"$mock_bin/chromium" <<'SH'
#!/bin/bash
[[ $1 != "--help" ]] || printf 'probed\n' >>"$ARCH_TEST_BROWSER_HELP"
SH
chmod +x "$mock_bin/chromium"
launch() {
  HOME="$test_home" PATH="$mock_bin:$PATH" ARCH_TEST_BROWSER_LAUNCH="$launch_log" \
    ARCH_TEST_BROWSER_FOCUS="$focus_log" ARCH_TEST_BROWSER_HELP="$help_log" \
    bash "$ROOT/src/arch/commands/arch-launch-browser" "$@"
}

launch "https://example.tests/a--private-b"
[[ ! -e $help_log ]] || fail "an ordinary launch doesn't probe the browser's flags"
grep -F 'https://example.tests/a--private-b' "$launch_log" >/dev/null || fail "an ordinary launch leaves its arguments alone"
pass "an ordinary launch doesn't probe the browser's flags"

launch --private
[[ -s $help_log ]] || fail "a private launch probes the browser's private flag"
grep -F -- 'chromium --incognito' "$launch_log" >/dev/null || fail "a private launch passes the browser's private flag"
pass "a private launch passes the browser's private flag"
