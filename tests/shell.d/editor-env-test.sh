#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

envs="$ROOT/default/bash/envs"

editor=$(env -u EDITOR bash -c 'source "$1"; printf "%s" "$EDITOR"' bash "$envs")
[[ $editor == "nvim" ]] || fail "bash env provides Neovim as the default editor" "actual: $editor"
pass "bash env provides a default editor"

editor=$(EDITOR=helix bash -c 'source "$1"; printf "%s" "$EDITOR"' bash "$envs")
[[ $editor == "helix" ]] || fail "bash env preserves the inherited editor" "actual: $editor"
pass "bash env preserves the inherited editor"

sudo_editor=$(env -u EDITOR -u SUDO_EDITOR bash -c 'source "$1"; printf "%s" "$SUDO_EDITOR"' bash "$envs")
[[ $sudo_editor == "nvim" ]] || fail "sudo uses the default editor" "actual: $sudo_editor"
pass "sudo uses the default editor"
