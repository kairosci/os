#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
require_command jq

migration="$ROOT/migrations/1791968925.sh"
split="$ROOT/migrations/1791969355.sh"
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT
config="$test_dir/home/.config/arch/shell.json"

run() {
  local script
  for script in "$@"; do
    env HOME="$test_dir/home" ARCH_PATH="$ROOT" bash -euo pipefail "$script" >"$test_dir/output" 2>&1 ||
      fail "migration runs" "$(cat "$test_dir/output")"
  done
}

# Writes a shell.json, runs the given migrations, and compares its bar to the
# expected one, ignoring key order.
check() {
  local given="$1" expected="$2" message="$3"
  shift 3
  mkdir -p "$(dirname "$config")"
  printf '%s\n' "$given" >"$config"
  run "${@:-$migration}"
  local actual wanted
  actual=$(jq -cS .bar "$config")
  wanted=$(jq -cS . <<<"$expected")
  [[ $actual == "$wanted" ]] || fail "$message" "$actual"
  pass "$message"
}

check '{"version":1,"bar":{"position":"top","layout":{"left":["arch.menu"],"center":["arch.clock"],"right":[{"id":"arch.keyboard-layout"},{"id":"arch.tray","pinned":["steam"]},{"id":"arch.agents"}]}}}' \
  '{"position":"top","layout":{"left":["arch.menu"],"center":["arch.clock"],"right":[{"id":"arch.tray","pinned":["steam"]},{"id":"arch.keyboard-layout"},{"id":"arch.agents"}]}}' \
  "a tray in the right section moves to its start, settings and all"

check '{"bar":{"layout":{"left":["arch.tray","arch.menu","arch.workspaces"]}}}' \
  '{"layout":{"left":["arch.menu","arch.workspaces","arch.tray"]}}' \
  "a tray in the left section moves to its end"

check '{"bar":{"layout":{"center":["arch.tray","arch.clock","arch.weather"]}}}' \
  '{"layout":{"center":["arch.clock","arch.weather","arch.tray"]}}' \
  "a tray in the center section moves to its end"

check '{"bar":{"layout":{"right":["a",{"id":"arch.tray","pinned":["x"]},"b","arch.tray"],"left":["arch.tray","c","arch.tray"]}}}' \
  '{"layout":{"right":["arch.tray","a","b"],"left":["c","arch.tray"]}}' \
  "only the last tray a section lists stays, as only it was drawn"

check '{"bar":{"id":"arch.bar","layout":{"right":["a","arch.tray"]}}}' \
  '{"id":"arch.bar","layout":{"right":["arch.tray","a"]}}' \
  "the built-in bar named by id is pinned like the default"

# The old bar pinned the tray and then split the center around its anchor, so
# a tray before the clock was drawn at the far end of what followed it.
# arch-migrate runs migrations in filename order.
[[ ${migration##*/} < ${split##*/} ]] || fail "the tray moves before the center is split"
pass "the tray moves before the center is split"
check '{"bar":{"centerAnchor":"arch.clock","layout":{"center":["arch.tray","arch.indicators","arch.clock","arch.weather"]}}}' \
  '{"layout":{"centerBegin":["arch.indicators"],"center":["arch.clock"],"centerEnd":["arch.weather","arch.tray"]}}' \
  "run before the center split, a tray before the anchor ends up where the bar drew it" \
  "$migration" "$split"

for given in \
  '{"version":1,"bar":{"layout":{"left":["arch.menu"],"right":["arch.tray","arch.audio"]}},"plugins":[]}' \
  '{"version":1,"bar":{"layout":{"right":["arch.audio"]}}}' \
  '{"version":1,"bar":{"id":"local.bar","layout":{"right":["arch.audio","arch.tray"]}}}' \
  '{"version":1,"bar":{"layout":{"right":"arch.tray"}}}' \
  '{"version":1,"bar":{"layout":["arch.tray"]}}' \
  '{"version":1}'; do
  printf '%s\n' "$given" >"$config"
  before=$(sha256sum "$config")
  run "$migration"
  [[ $(sha256sum "$config") == "$before" ]] || fail "a config with the tray already in place, without one, or for a replacement bar, is left byte for byte" "$given"
done
pass "a config with the tray already in place, without one, or for a replacement bar, is left byte for byte"

check '{"bar":{"layout":{"right":["a","arch.tray"]}}}' '{"layout":{"right":["arch.tray","a"]}}' "first run moves the tray"
run "$migration"
[[ $(jq -cS .bar "$config") == '{"layout":{"right":["arch.tray","a"]}}' ]] ||
  fail "a second run changes nothing" "$(jq -cS .bar "$config")"
pass "a second run changes nothing"

rm -f "$config"
run "$migration"
[[ ! -e $config ]] || fail "without a shell.json the migration writes none"
pass "without a shell.json the migration writes none"
