#!/bin/bash

# Give theme switching and upgrade tests their historical palettes and backgrounds
# without exposing those themes in the installed theme picker.
use_theme_fixtures() {
  local fixture_root="$1/theme-fixture-root" entry
  mkdir -p "$fixture_root"
  for entry in "$ROOT"/*; do
    if [[ ${entry##*/} != "assets" ]]; then
      ln -s "$entry" "$fixture_root/${entry##*/}"
    fi
  done
  mkdir -p "$fixture_root/assets"
  for entry in "$ROOT"/assets/*; do
    if [[ ${entry##*/} != "themes" ]]; then
      ln -s "$entry" "$fixture_root/assets/${entry##*/}"
    fi
  done
  ln -s "$ROOT/test/fixtures/themes" "$fixture_root/assets/themes"
  ln -s "$ROOT/test/fixtures/themes" "$fixture_root/themes"
  ROOT="$fixture_root"
}
