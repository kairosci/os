#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"
require_command jq

migration="$ROOT/migrations/1791969355.sh"
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT
config="$test_dir/home/.config/arch/shell.json"

run() {
  env HOME="$test_dir/home" ARCH_PATH="$ROOT" bash -euo pipefail "$migration" >"$test_dir/output" 2>&1 ||
    fail "migration runs" "$(cat "$test_dir/output")"
}

# Writes a shell.json, runs the migration, and compares its bar to the expected
# one, ignoring key order.
check() {
  local given="$1" expected="$2" message="$3"
  mkdir -p "$(dirname "$config")"
  printf '%s\n' "$given" >"$config"
  run
  local actual wanted
  actual=$(jq -cS .bar "$config")
  wanted=$(jq -cS . <<<"$expected")
  [[ $actual == "$wanted" ]] || fail "$message" "$actual"
  pass "$message"
}

check '{"version":1,"bar":{"position":"top","centerAnchor":"arch.clock","layout":{"left":["arch.menu"],"center":[{"id":"arch.indicators"},{"id":"arch.clock","format":"HH:mm"},{"id":"arch.elsewhen","zones":"Tokyo"},"arch.weather"],"right":[]}}}' \
  '{"position":"top","layout":{"left":["arch.menu"],"centerBegin":[{"id":"arch.indicators"}],"center":[{"id":"arch.clock","format":"HH:mm"}],"centerEnd":[{"id":"arch.elsewhen","zones":"Tokyo"},"arch.weather"],"right":[]}}' \
  "the anchor stays in the box and what flanked it moves to the sections either side, settings and all"

check '{"bar":{"centerAnchor":"arch.clock","layout":{"center":["arch.clock","arch.weather"]}}}' \
  '{"layout":{"centerBegin":[],"center":["arch.clock"],"centerEnd":["arch.weather"]}}' \
  "an anchor at the start of the center leaves centerBegin empty"

check '{"bar":{"centerAnchor":"arch.clock","layout":{"center":["arch.media","arch.clock"]}}}' \
  '{"layout":{"centerBegin":["arch.media"],"center":["arch.clock"],"centerEnd":[]}}' \
  "an anchor at the end of the center leaves centerEnd empty"

check '{"bar":{"centerAnchor":"","layout":{"center":["arch.media","arch.clock"]}}}' \
  '{"layout":{"center":["arch.media","arch.clock"]}}' \
  "a center without an anchor was centered as one group and stays whole in the box"

check '{"bar":{"centerAnchor":"arch.clock","layout":{"left":["arch.clock"],"center":["arch.media","arch.weather"]}}}' \
  '{"layout":{"left":["arch.clock"],"center":["arch.media","arch.weather"]}}' \
  "an anchor the center does not hold leaves the center whole in the box"

check '{"bar":{"centerAnchor":"arch.clock","layout":{"center":["arch.clock","arch.media","arch.clock"]}}}' \
  '{"layout":{"centerBegin":[],"center":["arch.clock"],"centerEnd":["arch.media","arch.clock"]}}' \
  "a repeated anchor splits at its first entry, as the bar drew it"

check '{"bar":{"centerAnchor":"arch.clock","layout":{"centerBegin":["a"],"center":["b","arch.clock","c"],"centerEnd":["d"]}}}' \
  '{"layout":{"centerBegin":["a","b"],"center":["arch.clock"],"centerEnd":["c","d"]}}' \
  "entries already in centerBegin and centerEnd keep their places on the outside"

check '{"bar":{"centerAnchor":"arch.clock","id":"arch.bar","layout":{"center":["a","arch.clock","b"]}}}' \
  '{"id":"arch.bar","layout":{"centerBegin":["a"],"center":["arch.clock"],"centerEnd":["b"]}}' \
  "the built-in bar named by id is split like the default"

check '{"bar":{"centerAnchor":"arch.clock","id":"","layout":{"center":["a","arch.clock"]}}}' \
  '{"id":"","layout":{"centerBegin":["a"],"center":["arch.clock"],"centerEnd":[]}}' \
  "an empty bar id means the built-in bar, as it does to the shell"

check '{"bar":{"centerAnchor":"arch.clock","layout":["arch.clock"]}}' \
  '{"layout":["arch.clock"]}' \
  "a layout that is not an object only loses the anchor, and the queue moves on"

check '{"bar":{"centerAnchor":"arch.clock","layout":{"center":"arch.clock"}}}' \
  '{"layout":{"center":"arch.clock"}}' \
  "a center that is not a list only loses the anchor"

for given in \
  '{"version":1,"bar":{"layout":{"center":["arch.media","arch.clock"]}},"plugins":[]}' \
  '{"version":1,"bar":{"id":"local.bar","centerAnchor":"arch.clock","layout":{"center":["a","arch.clock","b"]}}}'; do
  printf '%s\n' "$given" >"$config"
  before=$(sha256sum "$config")
  run
  [[ $(sha256sum "$config") == "$before" ]] || fail "a config without centerAnchor, or for a replacement bar, is left byte for byte" "$given"
done
pass "a config without centerAnchor, or for a replacement bar, is left byte for byte"

check '{"bar":{"centerAnchor":"arch.clock","layout":{"center":["a","arch.clock","b"]}}}' \
  '{"layout":{"centerBegin":["a"],"center":["arch.clock"],"centerEnd":["b"]}}' \
  "first run splits the center"
run
[[ $(jq -cS .bar "$config") == '{"layout":{"center":["arch.clock"],"centerBegin":["a"],"centerEnd":["b"]}}' ]] ||
  fail "a second run changes nothing" "$(jq -cS .bar "$config")"
pass "a second run changes nothing"

rm -f "$config"
run
[[ ! -e $config ]] || fail "without a shell.json the migration writes none"
pass "without a shell.json the migration writes none"
