#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/base-test.sh"

generator="$ROOT/src/arch/commands/arch-locale-generate"
language="$ROOT/src/arch/commands/arch-language"
sudoers_file="$ROOT/etc/sudoers.d/arch-locale-generate"
registry="$ROOT/default/i18n/locales.json"

# Exactly one rule, naming each registry code as the whole argument. A code
# missing would prompt again for that language; the command with its argument
# dropped, which sudoers reads as "any arguments", would widen the grant.
expected="%wheel ALL=(root) NOPASSWD: $(jq -r 'keys | sort | map("/usr/bin/arch-locale-generate " + .) | join(", ")' "$registry")"
rules=$(grep -vE '^[[:space:]]*(#|$)' "$sudoers_file")
[[ $rules == "$expected" ]] ||
  fail "locale sudoers file carries exactly one rule naming each registry code" "got: $rules"

if command -v visudo >/dev/null; then
  visudo -cf "$sudoers_file" >/dev/null || fail "locale sudoers rule parses"
fi
pass "locale sudoers rule is scoped to the registry's languages"

grep -Fx 'generator=/usr/bin/arch-locale-generate' "$language" >/dev/null ||
  fail "arch-language elevates the path the sudoers rule names"
# `sudo -l` alone says whether a command is permitted, which os's blanket
# %wheel rule answers yes to; only the long listing prints the entry's tags.
grep -E 'sudo -n -l -l' "$language" >/dev/null ||
  fail "arch-language reads the grant from the long sudo listing"
pass "arch-language asks sudo for the grant before prompting"

# Root resolves bare helpers under sudo's secure_path, which a dev link
# prepends a user-writable checkout bin/ to, so the helper pins PATH to system
# directories once it holds root, and only then.
gated=$(grep -A1 -E '^if \(\( EUID == 0 \)\); then$' "$generator" || true)
[[ $gated == *"export PATH=/usr/local/sbin:/usr/local/bin:/usr/bin"* ]] ||
  fail "arch-locale-generate gates the trusted-PATH pin on holding root"
# The test overrides must never reach root: root reads the packaged registry
# and the real locale.gen.
overrides=$(sed -n '/^if (( EUID != 0 )); then$/,/^fi$/p' "$generator")
[[ $overrides == *'ARCH_LOCALE_REGISTRY'* && $overrides == *'ARCH_LOCALE_GEN'* ]] ||
  fail "arch-locale-generate honors its test overrides only without root"
pass "arch-locale-generate pins PATH and its files when it holds root"

# Unprivileged runs against fixtures: locale-gen is stubbed, the registry and
# locale.gen are overridden.
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/bin"
cat >"$work/bin/locale-gen" <<'STUB'
#!/bin/bash
echo "$@" >>"$LOCALE_GEN_LOG"
STUB
chmod +x "$work/bin/locale-gen"
export LOCALE_GEN_LOG=$work/locale-gen.log ARCH_LOCALE_GEN=$work/locale.gen ARCH_LOCALE_REGISTRY=$registry
printf '#sv_SE.UTF-8 UTF-8\n#hi_IN UTF-8\n' >"$ARCH_LOCALE_GEN"
run() { PATH="$work/bin:$PATH" bash "$generator" "$@"; }

: >"$LOCALE_GEN_LOG"
run fr || fail "arch-locale-generate generates a supported language"
grep -qx 'fr_FR.UTF-8 UTF-8' "$ARCH_LOCALE_GEN" || fail "the language's locale is enabled in locale.gen" "$(cat "$ARCH_LOCALE_GEN")"
[[ $(cat "$LOCALE_GEN_LOG") == "fr_FR.UTF-8" ]] || fail "locale-gen generates the language's locale" "$(cat "$LOCALE_GEN_LOG")"
: >"$LOCALE_GEN_LOG"
run es || fail "arch-locale-generate adds a supported locale locale.gen doesn't list"
grep -qx 'es_ES.UTF-8 UTF-8' "$ARCH_LOCALE_GEN" || fail "a missing locale is appended to locale.gen" "$(cat "$ARCH_LOCALE_GEN")"
pass "arch-locale-generate enables and generates supported language locales"

for bad in "" "xx" "sv" "../fr" "fr;id" "fr es" "FR"; do
  : >"$LOCALE_GEN_LOG"
  if run "$bad" 2>/dev/null; then
    fail "arch-locale-generate rejects '$bad'"
  fi
  [[ ! -s $LOCALE_GEN_LOG ]] || fail "a rejected code generates nothing" "'$bad'"
done
if run fr es 2>/dev/null; then
  fail "arch-locale-generate takes exactly one code"
fi
pass "arch-locale-generate rejects anything but one registry code"

# The registry decides the locale; a malformed one never reaches locale.gen.
printf '{"fr": {"locale": "fr_FR.UTF-8 UTF-8\\nes_ES.UTF-8"}}\n' >"$work/registry.json"
: >"$LOCALE_GEN_LOG"
if ARCH_LOCALE_REGISTRY=$work/registry.json run fr 2>/dev/null; then
  fail "arch-locale-generate rejects a malformed registry locale"
fi
[[ ! -s $LOCALE_GEN_LOG ]] || fail "a malformed registry locale generates nothing"
pass "arch-locale-generate only generates well-formed locales"
