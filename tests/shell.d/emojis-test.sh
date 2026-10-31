#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

run_node_test <<'JS'
const fs = require('fs')
const emojis = requireFromRoot('src/arch/shell/plugins/emojis/EmojiSearch.js')

const raw = fs.readFileSync(path.join(root, 'src/arch/shell/plugins/emojis/emojis.json'), 'utf8')
const data = emojis.parseEmojis(raw)

assert(data.length > 1000, 'emoji dataset parses')
assertDeepEqual(emojis.parseEmojis('{'), [], 'invalid emoji JSON parses as empty list')
assertDeepEqual(emojis.parseEmojis('{"e":"nope"}'), [], 'non-array emoji JSON parses as empty list')

const fixture = [
  { e: 'a', k: 'grinning face smile happy' },
  { e: 'b', k: 'face with tears of joy joy tears' },
  { e: 'c', k: 'flag: united states us america' }
]

assertDeepEqual(
  emojis.filterEmojis(fixture, '  JOY  ').map(item => item.e),
  ['b'],
  'emoji filtering trims and lowercases query'
)

assertDeepEqual(
  emojis.filterEmojis(fixture, '', 2).map(item => item.e),
  ['a', 'b'],
  'emoji filtering honors result limit'
)

assertDeepEqual(
  emojis.filterEmojis(fixture, '', 0),
  [],
  'emoji filtering supports zero result limit'
)

assertEqual(
  emojis.filterEmojis(data, 'face with tears')[0].e,
  '\u{1F602}',
  'emoji filtering finds face with tears of joy'
)
JS

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

mkdir -p "$TMPDIR/bin"

cat >"$TMPDIR/bin/wl-copy" <<'SH'
#!/bin/bash
args="$*"
target="$WL_COPY_OUT"
if [[ $args == "--type text/plain --sensitive --foreground" ]]; then
  target="$WL_COPY_EMOJI_OUT"
fi

printf '%s\n' "$args" >"$target.args"
cat >"$target"
printf '%s\n' "$BASHPID" >"$WL_COPY_PID_OUT"
trap 'kill "$provider_child" 2>/dev/null || true; wait "$provider_child" 2>/dev/null || true; : >"$WL_COPY_STOPPED"; exit 0' TERM
/usr/bin/sleep 30 &
provider_child=$!
wait "$provider_child"
SH

cat >"$TMPDIR/bin/wtype" <<'SH'
#!/bin/bash
printf '%s\n' "$*" >"$WTYPE_OUT"
if [[ ${WTYPE_BLOCK:-} == 1 ]]; then
  trap 'kill "$paste_child" 2>/dev/null || true; wait "$paste_child" 2>/dev/null || true; : >"$WTYPE_STOPPED"; exit 0' TERM
  /usr/bin/sleep 30 &
  paste_child=$!
  wait "$paste_child"
fi
SH

chmod +x "$TMPDIR/bin/wl-copy" "$TMPDIR/bin/wtype"

WL_COPY_OUT="$TMPDIR/copy" WL_COPY_EMOJI_OUT="$TMPDIR/emoji" WTYPE_OUT="$TMPDIR/wtype" \
WL_COPY_PID_OUT="$TMPDIR/provider.pid" WL_COPY_STOPPED="$TMPDIR/provider.stopped" \
  AP="$ROOT" PATH="$TMPDIR/bin:$PATH" archctl menu emoji insert "😀"

[[ $(<"$TMPDIR/emoji") == "😀" ]] || fail "emoji insert helper copies emoji transiently"
pass "emoji insert helper copies emoji transiently"

[[ $(<"$TMPDIR/emoji.args") == "--type text/plain --sensitive --foreground" ]] || fail "emoji insert helper serves sensitive transient clipboard in foreground"
pass "emoji insert helper serves transient clipboard in foreground"

[[ $(<"$TMPDIR/wtype") == "-M shift -k Insert -m shift" ]] || fail "emoji insert helper pastes with shift insert"
pass "emoji insert helper pastes with shift insert"

[[ -f $TMPDIR/provider.stopped ]] || fail "emoji insert helper terminates the transient clipboard provider"
pass "emoji insert helper terminates its clipboard process group"

rm -f "$TMPDIR/provider.pid" "$TMPDIR/provider.stopped" "$TMPDIR/wtype"
AP="$ROOT" PATH="$TMPDIR/bin:$PATH" \
  archctl menu emoji insert "" || fail "empty emoji input remains a no-op"
[[ ! -e $TMPDIR/provider.pid && ! -e $TMPDIR/wtype ]] || fail "empty emoji input starts no helper processes"
pass "empty emoji input starts no helper processes"

oversized=$(printf '%4097s' x)
status=0
AP="$ROOT" PATH="$TMPDIR/bin:$PATH" archctl menu emoji insert "$oversized" 2>/dev/null || status=$?
[[ $status == 1 && ! -e $TMPDIR/provider.pid ]] || fail "oversized emoji input fails before starting the clipboard provider"
pass "oversized emoji input is rejected before process startup"

rm -f "$TMPDIR/provider.pid" "$TMPDIR/provider.stopped" "$TMPDIR/wtype" "$TMPDIR/wtype.stopped"
WTYPE_BLOCK=1 WTYPE_STOPPED="$TMPDIR/wtype.stopped" \
WL_COPY_OUT="$TMPDIR/copy" WL_COPY_EMOJI_OUT="$TMPDIR/emoji" WTYPE_OUT="$TMPDIR/wtype" \
WL_COPY_PID_OUT="$TMPDIR/provider.pid" WL_COPY_STOPPED="$TMPDIR/provider.stopped" \
  AP="$ROOT" PATH="$TMPDIR/bin:$PATH" archctl menu emoji insert "😀" &
insert_pid=$!
for ((attempt = 0; attempt < 100; attempt++)); do
  [[ -f $TMPDIR/wtype ]] && break
  /usr/bin/sleep 0.02
done
[[ -f $TMPDIR/wtype ]] || fail "emoji insert helper starts paste process for termination test"
kill -TERM "$insert_pid"
status=0
wait "$insert_pid" || status=$?
[[ $status == 143 && -f $TMPDIR/provider.stopped && -f $TMPDIR/wtype.stopped ]] || fail "termination cleans up clipboard and paste process groups"
pass "termination cleans up clipboard and paste process groups"
