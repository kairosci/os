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

cat >"$mock_bin/arch-theme-bg-set" <<'SH'
#!/bin/bash
printf '%s\n' "$1" >>"$ARCH_TEST_BACKGROUND_CALLS"
SH
chmod +x "$mock_bin/arch-theme-bg-set"

cat >"$mock_bin/arch-i18n" <<'SH'
#!/bin/bash
[[ $1 == "theme.noBackground" ]] || exit 1
printf 'No background\n'
SH
chmod +x "$mock_bin/arch-i18n"

cat >"$mock_bin/arch-notification-send" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$ARCH_TEST_BACKGROUND_NOTIFICATIONS"
SH
chmod +x "$mock_bin/arch-notification-send"

cat >"$mock_bin/arch-shell" <<'SH'
#!/bin/bash
printf '%s\n' "$@" >>"$ARCH_TEST_BACKGROUND_SHELL_CALLS"
SH
chmod +x "$mock_bin/arch-shell"

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
  python3 -I "$ROOT/src/arch/python/installer_user/setup/theme.py"
grep -Fx 'Cosmic' "$calls" >/dev/null || fail "user theme setup seeds Cosmic when no theme exists"
[[ -f $test_tmp/home/.config/chromium/SingletonLock ]] || fail "runtime user theme setup preserves Chromium's singleton lock"

: >"$calls"
printf 'Solitude\n' >"$test_tmp/home/.local/state/arch/current/theme.name"
HOME="$test_tmp/home" ARCH_PATH="$ROOT" PATH="$mock_bin:$PATH" ARCH_TEST_THEME_CALLS="$calls" \
  python3 -I "$ROOT/src/arch/python/installer_user/setup/theme.py"
[[ ! -s $calls ]] || fail "user theme setup preserves an existing theme"

pass "user theme setup only seeds the default theme once"

mkdir -p "$test_tmp/home/.local/state/arch/current" \
  "$test_tmp/home/.config/arch/themes/tokyo-night" \
  "$test_tmp/theme-arch/src/arch/cli/theme" \
  "$test_tmp/theme-arch/data/cli" \
  "$test_tmp/theme-arch/assets/themes/cosmic-night" \
  "$test_tmp/theme-arch/assets/themes/blue-sky"
mkdir -p "$test_tmp/home/.config/arch/themes/cosmic-night"
ln -s missing-theme "$test_tmp/home/.config/arch/themes/user-linked-theme"
ln -s cosmic-night "$test_tmp/theme-arch/assets/themes/bundled-link"
cp "$ROOT/src/arch/cli/theme/info.py" "$test_tmp/theme-arch/src/arch/cli/theme/info.py"
cp "$ROOT/data/cli/theme-info.yml" "$test_tmp/theme-arch/data/cli/theme-info.yml"
printf 'tokyo-night\n' >"$test_tmp/home/.local/state/arch/current/theme.name"
current=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/arch/commands/arch-theme-current")
[[ $current == "Tokyo Night" ]] || fail "current theme output keeps the theme's display name" "$current"
pass "current theme name is rendered"

rm "$test_tmp/home/.local/state/arch/current/theme.name"
current=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/arch/commands/arch-theme-current")
[[ $current == "Sconosciuto" ]] || fail "missing current theme is localized" "$current"
pass "missing current theme uses the selected locale"
printf 'tokyo-night\n' >"$test_tmp/home/.local/state/arch/current/theme.name"

user_dir=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/arch/commands/arch-theme-dir" tokyo-night)
[[ $user_dir == "$test_tmp/home/.config/arch/themes/tokyo-night" ]] || fail "theme directory prefers the user-installed copy" "$user_dir"
bundled_dir=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" \
  "$ROOT/src/arch/commands/arch-theme-dir" blue-sky)
[[ $bundled_dir == "$test_tmp/theme-arch/assets/themes/blue-sky" ]] || fail "theme directory falls back to the bundled copy" "$bundled_dir"
if HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/arch/commands/arch-theme-dir" ../../etc >"$test_tmp/theme-dir.out" 2>"$test_tmp/theme-dir.err"; then
  fail "theme directory rejects path traversal"
fi
grep -Fx 'Uso: arch-theme-dir <nome-tema>' "$test_tmp/theme-dir.err" >/dev/null ||
  fail "theme directory usage is localized"
[[ ! -s $test_tmp/theme-dir.out ]] || fail "theme directory prints no path for invalid input"
pass "theme directory prefers user themes, falls back to bundled themes and rejects traversal"

theme_list=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" "$ROOT/src/arch/commands/arch-theme-list")
[[ $theme_list == $'Blue Sky\nCosmic Night\nTokyo Night\nUser Linked Theme' ]] || fail "theme list merges theme directories and user symlinks in sorted order" "$theme_list"
pass "theme list merges bundled and user themes in sorted order"

printf 'wallpaper\n' >"$test_tmp/theme-arch/assets/themes/cosmic-night/004-sunset-glow.jpg"
ln -s "$test_tmp/theme-arch/assets/themes/cosmic-night/004-sunset-glow.jpg" \
  "$test_tmp/home/.local/state/arch/current/background"
background=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" \
  "$ROOT/src/arch/commands/arch-theme-bg-current")
[[ $background == "Sunset Glow" ]] || fail "current background resolves and formats the selected filename" "$background"
pass "current background name is formatted"

rm "$test_tmp/home/.local/state/arch/current/background"
background=$(HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/arch/commands/arch-theme-bg-current")
[[ $background == "Sconosciuto" ]] || fail "missing current background is localized" "$background"
pass "missing current background uses the selected locale"

user_backgrounds="$test_tmp/home/.config/arch/backgrounds/tokyo-night"
theme_backgrounds="$test_tmp/home/.local/state/arch/current/theme/backgrounds"
mkdir -p "$user_backgrounds" "$theme_backgrounds"
printf 'first\n' >"$user_backgrounds/000-first.jpg"
printf 'second\n' >"$user_backgrounds/002-second.MP4"
printf 'theme\n' >"$theme_backgrounds/001-theme.webp"
ln -s "$user_backgrounds/000-first.jpg" "$test_tmp/home/.local/state/arch/current/background"
background_calls="$test_tmp/background-calls"
background_notifications="$test_tmp/background-notifications"
HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" PATH="$mock_bin:$PATH" \
  ARCH_TEST_BACKGROUND_CALLS="$background_calls" \
  ARCH_TEST_BACKGROUND_NOTIFICATIONS="$background_notifications" \
  "$ROOT/src/arch/commands/arch-theme-bg-next"
grep -Fx "$user_backgrounds/002-second.MP4" "$background_calls" >/dev/null ||
  fail "background cycling advances in sorted order across supported media" "$(cat "$background_calls")"
pass "background cycling advances to the next sorted supported media"

mkdir -p "$test_tmp/home/.config/outside"
printf 'untrusted\n' >"$test_tmp/home/.config/outside/000-untrusted.jpg"
printf 'safe\n' >"$theme_backgrounds/010-safe.jpg"
printf '../../outside\n' >"$test_tmp/home/.local/state/arch/current/theme.name"
rm "$test_tmp/home/.local/state/arch/current/background"
: >"$background_calls"
HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" PATH="$mock_bin:$PATH" \
  ARCH_TEST_BACKGROUND_CALLS="$background_calls" \
  ARCH_TEST_BACKGROUND_NOTIFICATIONS="$background_notifications" \
  "$ROOT/src/arch/commands/arch-theme-bg-next"
grep -Fx "$theme_backgrounds/001-theme.webp" "$background_calls" >/dev/null ||
  fail "invalid theme ids cannot redirect background discovery outside the theme directory" "$(cat "$background_calls")"
pass "invalid theme ids cannot redirect background discovery"

rm -f "$user_backgrounds/000-first.jpg" "$user_backgrounds/002-second.MP4" "$theme_backgrounds/001-theme.webp"
rm -f "$theme_backgrounds/010-safe.jpg"
: >"$background_notifications"
HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" PATH="$mock_bin:$PATH" \
  ARCH_TEST_BACKGROUND_CALLS="$background_calls" \
  ARCH_TEST_BACKGROUND_NOTIFICATIONS="$background_notifications" \
  "$ROOT/src/arch/commands/arch-theme-bg-next"
grep -Fx 'No background -t 2000' "$background_notifications" >/dev/null ||
  fail "empty background list sends the translated notification" "$(cat "$background_notifications")"
[[ $(wc -l <"$background_calls") == 1 ]] || fail "empty background list does not change the selected background"
pass "empty background list sends the translated notification"

selected_background="$test_tmp/theme-arch/assets/themes/cosmic-night/selected image.png"
printf 'image\n' >"$selected_background"
shell_calls="$test_tmp/background-shell-calls"
HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" PATH="$mock_bin:$PATH" \
  ARCH_TEST_BACKGROUND_SHELL_CALLS="$shell_calls" \
  "$ROOT/src/arch/commands/arch-theme-bg-set" "$selected_background"
[[ $(readlink "$test_tmp/home/.local/state/arch/current/background") == "$selected_background" ]] ||
  fail "background setter atomically selects the resolved media path"
[[ $(cat "$shell_calls") == $'-q\nbackground\nset\n'"$selected_background" ]] ||
  fail "background setter refreshes the live shell with one quoted path argument" "$(cat "$shell_calls")"
[[ -z $(find "$test_tmp/home/.local/state/arch/current" -mindepth 1 -maxdepth 1 -type d -name '.background-*' -print -quit) ]] ||
  fail "background setter cleans up its temporary directory"
pass "background setter atomically selects media and refreshes the shell"

if HOME="$test_tmp/home" ARCH_PATH="$test_tmp/theme-arch" LC_ALL= LC_MESSAGES=it_IT.UTF-8 \
  "$ROOT/src/arch/commands/arch-theme-bg-set" "$test_tmp/missing.png" >"$test_tmp/background-set.out" 2>"$test_tmp/background-set.err"; then
  fail "background setter rejects a missing file"
fi
grep -F 'Il file non esiste:' "$test_tmp/background-set.err" >/dev/null ||
  fail "background setter localizes missing-file errors"
[[ $(readlink "$test_tmp/home/.local/state/arch/current/background") == "$selected_background" ]] ||
  fail "background setter leaves the current link unchanged when validation fails"
pass "background setter rejects missing files without changing the selection"
