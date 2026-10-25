#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

# Start with color enabled; the no-color scenarios opt in below.
unset NO_COLOR

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

# The launcher ends by taking over the process, so source it short of that line
# and exercise its animation logic without opening a terminal.
about="$ROOT/bin/arch-launch-about"
grep -q -- '--app-id=org.arch.about' "$about" || fail "About uses the Arch app id"
pass "About uses the Arch app id"
grep -q '^if \[\[ ${1:-} == "--render" \]\]; then$' "$about" || fail "About launcher can be sourced short of its launch"
sed '/^if \[\[ ${1:-} == "--render" \]\]; then$/,$d' "$about" >"$tmp_dir/about.bash"

export HOME="$tmp_dir/home"
export PATH="$ROOT/bin:$PATH"
mkdir -p "$HOME/.config/arch/branding"
printf '%s\n' '████████' '████████' >"$HOME/.config/arch/branding/screensaver.txt"

source "$tmp_dir/about.bash"
[[ $(type -t sheen_build) == "function" ]] || fail "the launcher finds the sheen it sources"
pass "the launcher finds the sheen it sources"

# Kept before the stubs replace it, so the real one can be exercised below.
real_measure_layout=$(declare -f measure_layout)

# Stand in for the terminal, and for the fastfetch run that measures the layout.
rows_by_cols="45 140"
layout_rows=20
logo_row=3
logo_column=3
logo_color=$'\e[1m\e[32m'
stty() { printf '%s\n' "$rows_by_cols"; }
measure_layout() {
  LAYOUT_ROWS=$layout_rows
  LOGO_COLOR=$logo_color
  LOGO_ROW=$logo_row
  LOGO_COLUMN=$logo_column
}

# fastfetch resolves the home directory from the passwd database rather than
# $HOME, so it would answer for the real one. Stand in for it with the search
# order it prints, pointed at this test's directories.
config_paths=(
  "$HOME/.config/fastfetch/"
  "$HOME/fastfetch/"
  "$ARCH_FASTFETCH_DIR/ (*)"
  "$HOME/searched-later/fastfetch/"
)
fastfetch() {
  [[ ${1:-} == "--list-config-paths" ]] || return 1
  printf '%s\n' "${config_paths[@]}"
}

# Record what the launcher hands the sheen rather than building any frames.
handed=()
sheen_build() { handed=("$@"); }

refuses() {
  if build_sheen; then
    fail "$1"
  else
    pass "$1"
  fi
}

build_sheen || fail "a roomy window animates"
pass "a roomy window animates"

# The sheen is told where the logo is, what colour to hand the cells back in, and
# how much room it has left of the module column.
[[ ${handed[0]} == "$HOME/.config/arch/branding/screensaver.txt" ]] || fail "the sheen is given the screensaver logo" "${handed[0]}"
pass "the sheen is given the logo About draws"
[[ ${handed[1]} == "$logo_row" && ${handed[2]} == "$logo_column" ]] || fail "the sheen is given the cell the logo starts on" "${handed[1]}/${handed[2]}"
pass "the sheen is given the cell the logo starts on"
[[ ${handed[3]} == $'\e[0m'"$logo_color" ]] || fail "the sheen is given fastfetch's own colour to restore" "$(printf '%q' "${handed[3]}")"
pass "the sheen is given fastfetch's own colour to restore"
[[ ${handed[4]} == "$((140 - logo_column + 1))" ]] || fail "the sheen is given the columns left of the module column" "${handed[4]}"
pass "the sheen is given the columns left of the module column"

# fastfetch reads the first config it finds across several directories, and any
# of them ahead of os's own can put the logo somewhere else entirely.
for directory in .config/fastfetch fastfetch; do
  mkdir -p "$HOME/$directory"
  touch "$HOME/$directory/config.jsonc"
  refuses "a fastfetch config in ~/$directory leaves the logo still"
  rm -r "${HOME:?}/$directory"
done

# One fastfetch would never read, because os's own comes first, is not a
# reason to stop: the logo on screen is still the one About drew.
mkdir -p "$HOME/searched-later/fastfetch"
touch "$HOME/searched-later/fastfetch/config.jsonc"
build_sheen || fail "a config fastfetch searches after os's own still animates"
pass "a config fastfetch searches after os's own still animates"
rm -r "${HOME:?}/searched-later"

# A window with no room for the cursor past the layout's last line has scrolled,
# and the logo is no longer on the rows the frames address.
rows_by_cols="$((layout_rows + 1)) 140"
build_sheen || fail "a window with one row past the layout animates"
pass "a window with one row past the layout animates"

rows_by_cols="$layout_rows 140"
refuses "a window level with the layout's last line leaves it still"
rows_by_cols="45 140"


# The loop plays whatever frames are left lying about, so a build that failed has
# to leave none of the last one's.
SHEEN_FRAMES=(stale frames)
NO_COLOR=1
build_sheen || true
unset NO_COLOR
(( ${#SHEEN_FRAMES[@]} == 0 )) || fail "a build that failed leaves no frames to replay" "${#SHEEN_FRAMES[@]} left"
pass "a build that failed leaves no frames to replay"

# fastfetch drops the logo's colour for a terminal that asked for none, but not
# for the measurement, so the colour to restore would be measured wrong — and a
# glint is colour besides.
NO_COLOR=1
refuses "a session that asked for no colour leaves the logo still"
unset NO_COLOR

# A home directory may contain a space, and the marker fastfetch puts beside the
# config it settled on is not part of the path.
spacey="$tmp_dir/example user/.config/fastfetch"
mkdir -p "$spacey"
touch "$spacey/config.jsonc"
config_paths=("$tmp_dir/example user/.config/fastfetch/" "$ARCH_FASTFETCH_DIR/ (*)")
custom_fastfetch_config || fail "a fastfetch config in a path with a space is found"
pass "a fastfetch config in a path with a space is found"
rm -r "$tmp_dir/example user"
config_paths=("$HOME/.config/fastfetch/" "$HOME/fastfetch/" "$ARCH_FASTFETCH_DIR/ (*)")

# An enumeration that said nothing is not the same answer as "none of them".
mkdir -p "$HOME/.config/fastfetch"
touch "$HOME/.config/fastfetch/config.jsonc"
listing=$(declare -f fastfetch)
fastfetch() { return 7; }
custom_fastfetch_config || fail "an enumeration that failed does not read as no config"
pass "an enumeration that failed does not read as no config"
eval "$listing"
rm -r "${HOME:?}/.config/fastfetch"

# The grid costs a process and is only read on the poll interval, so a resize can
# land while it is being read. The sweep has to see that before it paints again.
SHEEN_FRAMES=("first" "second" "third")
tick() { :; }
resized=false
content_changed() { resized=true; return 1; }
painted=$(play_sheen || true)
[[ -z $painted ]] || fail "a resize landing during the check stops the sweep before it paints" "$(printf '%q' "$painted")"
pass "a resize landing during the check stops the sweep before it paints"

resized=false
content_changed() { return 1; }
painted=$(play_sheen || true)
[[ $painted == "firstsecondthird" ]] || fail "an undisturbed sweep writes every frame" "$(printf '%q' "$painted")"
pass "an undisturbed sweep writes every frame"

# Every builder above can be exercised while nothing on screen ever animates, so
# check that the render loop is what calls them.
render_block=$(sed -n '/--render/,$p' "$about")
for called in build_sheen play_sheen rest_sheen; do
  [[ $render_block == *"$called"* ]] || fail "the render loop plays the sheen" "it never calls $called"
done
pass "the render loop plays the sheen"

measure_layout() { return 1; }
refuses "a layout fastfetch cannot be measured from leaves it still"

eval "$real_measure_layout"
LOGO_FILE="$tmp_dir/landmark.txt"
printf '%s\n' '████████' '██    ██' '████████' >"$LOGO_FILE"
render_with_padding() {
  local top=$1 left=$2 i line
  for (( i = 0; i < top; i++ )); do printf '\n'; done
  while IFS= read -r line; do printf '\e[1m\e[32m%*s%s\e[m\n' "$left" '' "$line"; done <"$LOGO_FILE"
  for (( i = 0; i < 6; i++ )); do printf 'module line\n'; done
}
for pad in "2 2" "4 5" "0 0" "6 10"; do
  set -- $pad
  eval "fastfetch() { render_with_padding $1 $2; }"
  LAYOUT_ROWS=""
  measure_layout || fail "the logo is found wherever fastfetch drew it" "padding $1/$2"
  [[ $LOGO_ROW == "$(( $1 + 1 ))" && $LOGO_COLUMN == "$(( $2 + 1 ))" ]] ||
    fail "the logo is found wherever fastfetch drew it" "padding $1/$2 measured $LOGO_ROW/$LOGO_COLUMN"
done
pass "the logo is found wherever fastfetch drew it"

# A render that does not contain the file's own text is not this logo, whatever
# the reason — a config that restyled it, a placeholder fastfetch substituted.
fastfetch() { printf 'something else entirely\n'; }
LAYOUT_ROWS=""
if measure_layout; then
  fail "a render without the logo in it is not measured"
else
  pass "a render without the logo in it is not measured"
fi

# About and other terminal TUIs stay tiled; the launcher must not resize or float them.
if grep -Eq 'org\.arch\.about|\|About\||TUI\.float' "$ROOT/default/hypr/apps/system.lua"; then
  fail "About has no floating window rule"
fi
if grep -Eq 'hyprctl|window\.resize|centerwindow|resizewindowpixel|window_rule|float' "$about"; then
  fail "About does not manipulate its window geometry"
fi
pass "terminal TUIs stay standard tiled windows"
