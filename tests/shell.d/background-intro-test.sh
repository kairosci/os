#!/bin/bash
set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
home="$work/home"
mkdir -p "$home"

HOME="$home" XDG_STATE_HOME="$work/state" ARCH_SESSION_ID=login-one "$ROOT/bin/arch-background-session-mark"
marker="$work/state/arch/background-intro.session-id"
[[ $(<"$marker") == login-one ]] || fail "a graphical login stores its session marker"
mtime=$(stat -c %Y "$marker")
sleep 1
HOME="$home" XDG_STATE_HOME="$work/state" ARCH_SESSION_ID=login-one "$ROOT/bin/arch-background-session-mark"
[[ $(stat -c %Y "$marker") == "$mtime" ]] || fail "a repeated shell start keeps the existing marker"
HOME="$home" XDG_STATE_HOME="$work/state" ARCH_SESSION_ID=login-two "$ROOT/bin/arch-background-session-mark"
[[ $(<"$marker") == login-two ]] || fail "a new graphical session replaces the marker"
pass "the native background session marker is idempotent across shell restarts"
