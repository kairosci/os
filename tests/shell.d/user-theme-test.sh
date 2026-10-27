#!/bin/bash

source "$(dirname "$0")/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT

mock_bin="$test_tmp/bin"
mkdir -p "$mock_bin" "$test_tmp/home/.config/chromium" "$test_tmp/home/.local/state/arch/current"

cat >"$mock_bin/arch-theme-set" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$ARCH_TEST_THEME_CALLS"
SH
chmod +x "$mock_bin/arch-theme-set"

for command in arch-theme-set-fcitx5; do
  cat >"$mock_bin/$command" <<'SH'
#!/bin/bash
exit 0
SH
  chmod +x "$mock_bin/$command"
done

calls="$test_tmp/theme-calls"
touch "$test_tmp/home/.config/chromium/SingletonLock"
HOME="$test_tmp/home" ARCH_PATH="$ROOT" PATH="$mock_bin:$PATH" ARCH_TEST_THEME_CALLS="$calls" \
  python3 -I "$ROOT/src/python/installer_user/setup/theme.py"
grep -Fx 'Cosmic' "$calls" >/dev/null || fail "user theme setup seeds Cosmic when no theme exists"
[[ -f $test_tmp/home/.config/chromium/SingletonLock ]] || fail "runtime user theme setup preserves Chromium's singleton lock"

: >"$calls"
printf 'Solitude\n' >"$test_tmp/home/.local/state/arch/current/theme.name"
HOME="$test_tmp/home" ARCH_PATH="$ROOT" PATH="$mock_bin:$PATH" ARCH_TEST_THEME_CALLS="$calls" \
  python3 -I "$ROOT/src/python/installer_user/setup/theme.py"
[[ ! -s $calls ]] || fail "user theme setup preserves an existing theme"

pass "user theme setup only seeds the default theme once"

mkdir -p "$test_tmp/home/.local/state/arch/current" \
  "$test_tmp/home/.config/arch/themes/tokyo-night" \
  "$test_tmp/theme-arch/src/python/cli" \
  "$test_tmp/theme-arch/data/cli" \
  "$test_tmp/theme-arch/assets/themes/cosmic-night" \
  "$test_tmp/theme-arch/assets/themes/blue-sky"
mkdir -p "$test_tmp/home/.config/arch/themes/cosmic-night"
ln -s missing-theme "$test_tmp/home/.config/arch/themes/user-linked-theme"
ln -s cosmic-night "$test_tmp/theme-arch/assets/themes/bundled-link"
cp "$ROOT/src/python/cli/theme_info.py" "$test_tmp/theme-arch/src/python/cli/theme_info.py"
cp "$ROOT/data/cli/theme-info.yml" "$test_tmp/theme-arch/data/cli/theme-info.yml"
printf 'tokyo-night\n' >"$test_tmp/home/.local/state/arch/current/theme.name"
current=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/cli/arch-theme-current")
[[ $current == "Tokyo Night" ]] || fail "current theme output keeps the theme's display name" "$current"
pass "current theme name is rendered"

rm "$test_tmp/home/.local/state/arch/current/theme.name"
current=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/cli/arch-theme-current")
[[ $current == "Sconosciuto" ]] || fail "missing current theme is localized" "$current"
pass "missing current theme uses the selected locale"
printf 'tokyo-night\n' >"$test_tmp/home/.local/state/arch/current/theme.name"

user_dir=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/cli/arch-theme-dir" tokyo-night)
[[ $user_dir == "$test_tmp/home/.config/arch/themes/tokyo-night" ]] || fail "theme directory prefers the user-installed copy" "$user_dir"
bundled_dir=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" \
  "$ROOT/src/cli/arch-theme-dir" blue-sky)
[[ $bundled_dir == "$test_tmp/theme-arch/assets/themes/blue-sky" ]] || fail "theme directory falls back to the bundled copy" "$bundled_dir"
if HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/cli/arch-theme-dir" ../../etc >"$test_tmp/theme-dir.out" 2>"$test_tmp/theme-dir.err"; then
  fail "theme directory rejects path traversal"
fi
grep -Fx 'Uso: arch-theme-dir <nome-tema>' "$test_tmp/theme-dir.err" >/dev/null ||
  fail "theme directory usage is localized"
[[ ! -s $test_tmp/theme-dir.out ]] || fail "theme directory prints no path for invalid input"
pass "theme directory prefers user themes, falls back to bundled themes and rejects traversal"

theme_list=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" "$ROOT/src/cli/arch-theme-list")
[[ $theme_list == $'Blue Sky\nCosmic Night\nTokyo Night\nUser Linked Theme' ]] || fail "theme list merges theme directories and user symlinks in sorted order" "$theme_list"
pass "theme list merges bundled and user themes in sorted order"

printf 'wallpaper\n' >"$test_tmp/theme-arch/assets/themes/cosmic-night/004-sunset-glow.jpg"
ln -s "$test_tmp/theme-arch/assets/themes/cosmic-night/004-sunset-glow.jpg" \
  "$test_tmp/home/.local/state/arch/current/background"
background=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" \
  "$ROOT/src/cli/arch-theme-bg-current")
[[ $background == "Sunset Glow" ]] || fail "current background resolves and formats the selected filename" "$background"
pass "current background name is formatted"

rm "$test_tmp/home/.local/state/arch/current/background"
background=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/cli/arch-theme-bg-current")
[[ $background == "Sconosciuto" ]] || fail "missing current background is localized" "$background"
pass "missing current background uses the selected locale"
