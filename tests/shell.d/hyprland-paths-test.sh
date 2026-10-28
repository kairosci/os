#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

require_command lua

run_paths() {
  lua - <<'LUA'
package.path = os.getenv("AP") .. "/?.lua;" .. package.path
local paths = require("default.hypr.paths")
assert(paths.config_home == os.getenv("EXPECTED_CONFIG"), "config_home: " .. paths.config_home)
assert(paths.state_home == os.getenv("EXPECTED_STATE"), "state_home: " .. paths.state_home)
LUA
}

HOME="/home/test-user" AP="$ROOT" \
  XDG_CONFIG_HOME= XDG_STATE_HOME= \
  EXPECTED_CONFIG="/home/test-user/.config" EXPECTED_STATE="/home/test-user/.local/state" \
  run_paths
pass "empty XDG path variables fall back to their defaults"

HOME="/home/test-user" AP="$ROOT" \
  XDG_CONFIG_HOME="/custom/config" XDG_STATE_HOME="/custom/state" \
  EXPECTED_CONFIG="/custom/config" EXPECTED_STATE="/custom/state" \
  run_paths
pass "set XDG path variables are honored"

ARCH_REPO="$ROOT" AP="$ROOT" lua - <<'LUA'
package.path = os.getenv("ARCH_REPO") .. "/?.lua;" .. package.path
_G.AP = "/usr/share/arch"
dofile(os.getenv("ARCH_REPO") .. "/default/hypr/bootstrap.lua")
local paths = dofile(os.getenv("ARCH_REPO") .. "/default/hypr/paths.lua")
assert(paths.ap == "/usr/share/arch", "ap: " .. paths.ap)
assert(package.path:find("/usr/share/arch/?.lua", 1, true), "package.path does not use the installed runtime")
assert(not package.path:find(os.getenv("ARCH_REPO") .. "/?.lua", 1, true), "package.path still uses the checkout")
LUA
pass "the home config can pin runtime defaults outside the checkout"
