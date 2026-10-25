#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

test_tmp=$(mktemp -d)
trap 'rm -rf "$test_tmp"' EXIT
home="$test_tmp/home with spaces"
stub_bin="$test_tmp/bin"
theme_dir="$home/.local/state/arch/current/theme"
icon_index="$test_tmp/icons/Cosmic/index.theme"
mkdir -p "$stub_bin" "$theme_dir" "$home/.config/gtk-3.0" "$(dirname "$icon_index")" "$home/.config/arch/icons/Cosmic"
cp "$ROOT/config/arch/icons/Cosmic/inherits" "$home/.config/arch/icons/Cosmic/inherits"
cat >"$icon_index" <<'EOF'
[Icon Theme]
Name=COSMIC
Inherits=Pop,hicolor
Directories=16x16/apps

[16x16/apps]
Size=16
Type=Fixed
EOF
mkdir -p "$home/.local/share/icons/Cosmic"
cp "$icon_index" "$home/.local/share/icons/Cosmic/index.theme"

cat >"$stub_bin/gsettings" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >>"$GNOME_TEST_GSETTINGS_LOG"
SH
cat >"$stub_bin/arch-theme-color" <<'SH'
#!/bin/bash
printf '%s\n' dark
SH
chmod +x "$stub_bin/"*

printf '%s\n' '@define-color cosmic_accent #cba6f7;' >"$theme_dir/gtk.css"
printf '%s\n' '/* User GTK settings */' 'button { padding: 4px; }' >"$home/.config/gtk-3.0/gtk.css"

run_theme() {
  HOME="$home" \
    XDG_CONFIG_HOME="$home/.config" \
    XDG_DATA_HOME="$home/.local/share" \
    ARCH_COSMIC_ICON_INDEX="$icon_index" \
    DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
    GNOME_TEST_GSETTINGS_LOG="$test_tmp/gsettings.log" \
    PATH="$stub_bin:$ROOT/src/cli:$PATH" \
    "$ROOT/src/cli/arch-theme-set-gnome"
}

run_theme
overlay="$home/.local/share/icons/Cosmic/index.theme"
grep -Fxq '# ARCH COSMIC FALLBACK OVERLAY' "$overlay" ||
  fail "Cosmic fallback is written as a marked user-owned icon overlay"
grep -Fxq 'Inherits=breeze-dark' "$overlay" ||
  fail "Cosmic uses Breeze Dark while Breeze provides the standard hicolor fallback"
grep -Fxq 'Directories=16x16/apps' "$overlay" ||
  fail "the user overlay keeps the Cosmic icon directory list"
grep -Fxq 'set org.gnome.desktop.interface icon-theme Cosmic' "$test_tmp/gsettings.log" ||
  fail "the configured Cosmic icon theme remains active"
pass "Cosmic icons retain their package directories and use the Breeze Dark fallback"

uri=$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).as_uri())' "$theme_dir/gtk.css")
grep -Fxq "@import url(\"$uri\");" "$home/.config/gtk-3.0/gtk.css" ||
  fail "GTK3 imports the current theme stylesheet with an escaped path"
grep -Fq 'button { padding: 4px; }' "$home/.config/gtk-3.0/gtk.css" ||
  fail "GTK3 user styles remain in place"
grep -Fxq "@import url(\"$uri\");" "$home/.config/gtk-4.0/gtk.css" ||
  fail "GTK4 imports the current theme stylesheet"
pass "GTK3 and GTK4 import the active theme while preserving user CSS"

run_theme
[[ $(grep -Fc 'ARCH THEME CSS BEGIN' "$home/.config/gtk-3.0/gtk.css") == 1 ]] ||
  fail "theme refresh replaces rather than duplicates its managed import"
pass "reapplying the GTK theme does not duplicate the stylesheet import"

rm "$theme_dir/gtk.css"
run_theme
! grep -q 'ARCH THEME CSS BEGIN' "$home/.config/gtk-3.0/gtk.css" ||
  fail "a theme without GTK CSS removes the old managed import"
grep -Fq 'button { padding: 4px; }' "$home/.config/gtk-3.0/gtk.css" ||
  fail "removing the managed import preserves user GTK styles"
pass "switching to a theme without GTK CSS removes only the managed import"

grep -Fxq 'set org.gnome.desktop.interface gtk-theme Breeze-Dark' "$test_tmp/gsettings.log" ||
  fail "dark mode keeps the installed GTK widget theme"
pass "GTK integration keeps the available dark widget theme"
