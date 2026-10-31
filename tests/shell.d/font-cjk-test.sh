#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
export AP=$ROOT XDG_CONFIG_HOME=$work/config NOTIFY_LOG=$work/notify.log
mkdir -p "$work/stubs"
printf '#!/bin/bash\n' >"$work/stubs/arch-restart-shell"
printf '#!/bin/bash\necho "$@" >>"$NOTIFY_LOG"\n' >"$work/stubs/arch-notification-send"
chmod +x "$work/stubs/"*
export PATH="$work/stubs:$ROOT/src/arch/commands:$PATH"
preference=$XDG_CONFIG_HOME/fontconfig/conf.d/50-arch-input-method.conf

[[ $(archctl font cjk) == "default" ]] || fail "with no preference the CJK forms are the default" "$(archctl font cjk)"
pass "with no preference the CJK forms are the default"

archctl font cjk tc
grep -q 'Noto Sans CJK TC' "$preference" || fail "setting tc writes the preference"
[[ $(archctl font cjk) == "tc" ]] || fail "the current forms read back as set" "$(archctl font cjk)"
grep -q "$(arch-i18n font.cjkChanged)" "$NOTIFY_LOG" || fail "a change is announced" "$(cat "$NOTIFY_LOG")"
pass "setting the CJK forms writes, reads back and announces the choice"

# A preference the first input method seeded reads back and can be changed.
rm "$preference"
python3 "$ROOT/default/input-methods/configure.py" font --seed kr
[[ $(archctl font cjk) == "kr" ]] || fail "a seeded preference reads back" "$(archctl font cjk)"
archctl font cjk hk
[[ $(archctl font cjk) == "hk" ]] || fail "a seeded preference can be changed" "$(archctl font cjk)"
pass "the preference an input method seeded is the one the command changes"

archctl font cjk default
[[ $(archctl font cjk) == "default" ]] || fail "default reads back" "$(archctl font cjk)"
! grep -q 'CJK' "$preference" || fail "default names no CJK forms" "$(cat "$preference")"
python3 "$ROOT/default/input-methods/configure.py" font --seed kr
[[ $(archctl font cjk) == "default" ]] || fail "a later language or input method keeps an explicit default" "$(archctl font cjk)"
pass "default returns to the system's choice, and later seeding keeps it"

if archctl font cjk cn 2>/dev/null; then
  fail "an unknown variant is refused"
fi
pass "an unknown variant is refused"

mkdir -p "$work/invalid/data/cli"
printf '%s\n' 'commands: [' >"$work/invalid/data/cli/fonts.yml"
set +e
AP="$work/invalid" PYTHONPATH="$ROOT/src" python3 -c \
  'from arch.cli.font.catalog import cjk_main; raise SystemExit(cjk_main(["--help"]))' \
  >"$work/font-config.out" 2>"$work/font-config.err"
font_config_status=$?
set -e
(( font_config_status == 78 )) || fail "font command reports malformed settings at its command boundary"
grep -Fq 'Invalid CJK font configuration' "$work/font-config.err" || fail "font command explains malformed settings"
! grep -Fq 'Traceback' "$work/font-config.err" || fail "font command does not leak a traceback"
pass "font commands handle malformed YAML at their command boundary"

