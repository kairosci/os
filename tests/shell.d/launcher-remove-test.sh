#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

mkdir -p "$tmp_dir/data/applications" "$tmp_dir/system/applications" "$tmp_dir/bin"

write_fake_command() {
  local name="$1"
  local prefix="$2"

  cat >"$tmp_dir/bin/$name" <<SCRIPT
#!/bin/bash
printf '%s:%s:%s\\n' '$prefix' "\${ARCH_REMOVE_NOTIFY:-}" "\$*" >>"\$TEST_LOG"
SCRIPT
  chmod +x "$tmp_dir/bin/$name"
}

write_fake_command arch-webapp-remove web
write_fake_command arch-tui-remove tui
write_fake_command arch-launch-terminal-with-presentation terminal

cat >"$tmp_dir/bin/arch-notification-send" <<'SCRIPT'
#!/bin/bash
printf 'notify::%s\n' "$*" >>"$TEST_LOG"
SCRIPT
chmod +x "$tmp_dir/bin/arch-notification-send"

cat >"$tmp_dir/bin/update-desktop-database" <<'SCRIPT'
#!/bin/bash
:
SCRIPT
chmod +x "$tmp_dir/bin/update-desktop-database"

cat >"$tmp_dir/bin/pacman" <<'SCRIPT'
#!/bin/bash
if [[ $1 == "-Qqo" && $2 == */native.desktop ]]; then
  printf 'native-pkg\n'
fi
SCRIPT
chmod +x "$tmp_dir/bin/pacman"

cat >"$tmp_dir/data/applications/Basecamp.desktop" <<'DESKTOP'
[Desktop Entry]
Name=Basecamp
Exec=arch-launch-webapp https://example.com
DESKTOP

cat >"$tmp_dir/data/applications/Docker.desktop" <<'DESKTOP'
[Desktop Entry]
Name=Docker
Exec=xdg-terminal-exec --app-id=TUI.tile -e lazydocker
DESKTOP

cat >"$tmp_dir/system/applications/native.desktop" <<'DESKTOP'
[Desktop Entry]
Name=Native
Exec=native
DESKTOP

cat >"$tmp_dir/data/applications/aliens.desktop" <<'DESKTOP'
[Desktop Entry]
Name=Aliens
Exec=another-emulator --fullscreen /home/example/Games/library/example.rom
DESKTOP

export TEST_LOG="$tmp_dir/log"
export PATH="$tmp_dir/bin:$PATH"
export XDG_DATA_HOME="$tmp_dir/data"
export XDG_DATA_DIRS="$tmp_dir/system"

"$ROOT/src/arch/commands/arch-remove-launcher-entry" Basecamp.desktop Basecamp
"$ROOT/src/arch/commands/arch-remove-launcher-entry" Docker.desktop Docker
"$ROOT/src/arch/commands/arch-remove-launcher-entry" native.desktop Native
"$ROOT/src/arch/commands/arch-remove-launcher-entry" aliens.desktop Aliens

mapfile -t lines <"$TEST_LOG"

[[ ${lines[0]} == "web:false:Basecamp" ]] || fail "launcher remove routes web apps by desktop name" "${lines[0]}"
pass "launcher remove routes web apps by desktop name"

[[ ${lines[1]} == "tui:false:Docker" ]] || fail "launcher remove routes TUIs by desktop name" "${lines[1]}"
pass "launcher remove routes TUIs by desktop name"

[[ ${lines[2]} == "terminal::echo Uninstalling Native...; sudo pacman -Rns native-pkg" ]] || fail "launcher remove opens package uninstall flow" "${lines[2]}"
pass "launcher remove opens package uninstall flow"

[[ ! -e $tmp_dir/data/applications/aliens.desktop ]] || fail "launcher remove deletes user-owned desktop files"
pass "launcher remove deletes user-owned desktop files"

(( ${#lines[@]} == 3 )) || fail "launcher remove does not notify for user-owned desktop files" "$(printf '%s\n' "${lines[@]}")"
pass "launcher remove does not notify for user-owned desktop files"

cat >"$tmp_dir/bin/gtk-update-icon-cache" <<'SCRIPT'
#!/bin/bash
:
SCRIPT
chmod +x "$tmp_dir/bin/gtk-update-icon-cache"
cat >"$tmp_dir/icon.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><path d="M0 0h1v1H0z"/></svg>
SVG
ARCH_PATH="$ROOT" XDG_DATA_HOME="$tmp_dir/tui-data" \
  "$ROOT/src/arch/commands/arch-tui-install" "Example App" "printf 'hello world'" "$tmp_dir/icon.svg"
desktop="$tmp_dir/tui-data/applications/example-app.desktop"
icon="$tmp_dir/tui-data/icons/hicolor/256x256/apps/example-app.svg"
[[ -f $desktop && -f $icon ]] || fail "TUI install creates its desktop entry and local icon"
grep -Fx 'Name=Example App' "$desktop" >/dev/null || fail "TUI desktop entry keeps the launcher name"
grep -Fx 'Icon=example-app' "$desktop" >/dev/null || fail "TUI desktop entry uses its icon cache name"
grep -Fx 'Exec="xdg-terminal-exec" "--app-id=TUI.tile" "-e" "printf" "hello world"' "$desktop" >/dev/null ||
  fail "TUI desktop entry safely quotes the command and routes it through the terminal"
pass "TUI install writes a safely quoted launcher and installs a local icon"

invalid_root="$tmp_dir/invalid-arch-root"
mkdir -p "$invalid_root/data/cli"
ln -s "$ROOT/src" "$invalid_root/src"
printf 'commands: []\n' >"$invalid_root/data/cli/tui-install.yml"
invalid_output=""
invalid_status=0
invalid_output=$(ARCH_PATH="$invalid_root" "$ROOT/src/arch/commands/arch-tui-install" --help 2>&1) || invalid_status=$?
(( invalid_status == 78 )) || fail "invalid TUI installer settings have a configuration-error status" "$invalid_status: $invalid_output"
[[ $invalid_output == *"Could not load TUI installer settings:"* ]] ||
  fail "invalid TUI installer settings are reported at the command boundary" "$invalid_output"
[[ $invalid_output != *Traceback* ]] || fail "invalid TUI installer settings do not leak a traceback" "$invalid_output"
pass "TUI installer settings errors are handled at the command boundary"
