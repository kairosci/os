#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/base-test.sh"

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
mkdir -p "$tmpdir/bin"
for command in arch-pkg-add fc-cache arch-font-set; do
  cat >"$tmpdir/bin/$command" <<'STUB'
#!/bin/bash
printf '%s:%s\n' "${0##*/}" "$*" >>"$FONT_LOG"
STUB
  chmod +x "$tmpdir/bin/$command"
done
export FONT_LOG="$tmpdir/calls.log" PATH="$tmpdir/bin:$ROOT/src/cli:$PATH"

arch-install-font --apply ttf-example "Family Example"
grep -qxF 'arch-pkg-add:ttf-example' "$FONT_LOG" || fail "the selected Arch package is installed"
grep -qxF 'fc-cache:-f' "$FONT_LOG" || fail "fontconfig cache is refreshed"
grep -qxF 'arch-font-set:Family Example' "$FONT_LOG" || fail "the chosen family becomes the monospace default"
pass "preferred font installation and activation"

: >"$FONT_LOG"
if arch-install-font --apply 'ttf-example;touch /tmp/pwned' "Family Example" 2>/dev/null; then
  fail "package input cannot contain shell commands"
fi
if arch-install-font --apply ttf-example 'Family"</string><evil>' 2>/dev/null; then
  fail "font family input cannot inject XML"
fi
[[ ! -s $FONT_LOG ]] || fail "invalid font values are rejected before installation" "$(cat "$FONT_LOG")"
pass "font package and family input are validated before installation"
