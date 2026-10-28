#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

envs="$ROOT/default/bash/envs"
uwsm_default="$ROOT/default/uwsm/default"
uwsm_env="$ROOT/default/uwsm/env.d/10-arch"

browser=$(env -u BROWSER bash -c 'source "$1"; printf "%s" "$BROWSER"' bash "$envs")
[[ $browser == "arch-launch-browser" ]] || fail "bash env provides a default browser" "actual: $browser"
pass "bash env provides a default browser"

browser=$(BROWSER=firefox bash -c 'source "$1"; printf "%s" "$BROWSER"' bash "$envs")
[[ $browser == "firefox" ]] || fail "bash env preserves the inherited browser" "actual: $browser"
pass "bash env preserves the inherited browser"

# A session-wide BROWSER makes xdg-settings refuse "set default-web-browser",
# breaking the browsers' own "Set as default" buttons.
browser=$(env -u BROWSER bash -c 'source "$1"; printf "%s" "${BROWSER:-}"' bash "$uwsm_default")
[[ -z $browser ]] || fail "uwsm session env leaves BROWSER unset" "actual: $browser"
pass "uwsm session env leaves BROWSER unset"

! grep -q "export BROWSER" "$uwsm_env" || fail "uwsm env.d fallback leaves BROWSER unset"
pass "uwsm env.d fallback leaves BROWSER unset"

desktop_session=$(DESKTOP_SESSION=arch bash -c 'source "$1"; printf "%s" "$DESKTOP_SESSION"' bash "$uwsm_default")
[[ $desktop_session == "arch" ]] || fail "uwsm session identity uses Arch" "actual: $desktop_session"
pass "uwsm session identity uses Arch"

uwsm_path=$(AP="$ROOT" PATH="/usr/bin" bash -c 'source "$1"; printf "%s" "$PATH"' bash "$uwsm_default")
[[ ${uwsm_path%%:*} == "$ROOT/src/arch/commands" ]] || fail "uwsm prepends the checkout CLI" "actual PATH: $uwsm_path"
[[ $(tr ':' '\n' <<<"$uwsm_path" | grep -Fxc "$ROOT/src/arch/commands") == 1 ]] || fail "uwsm includes the checkout CLI once" "actual PATH: $uwsm_path"
pass "uwsm session PATH resolves the checkout CLI without duplication"
