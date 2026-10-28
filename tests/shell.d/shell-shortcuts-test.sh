#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

require_command lua

shortcuts="$ROOT/default/arch/shortcuts"

# Load the helpers and every default binding against a stub hl, and print one
# line per binding: "global <name>" for a global shortcut, "exec <command>" for
# a command, then its description.
list_bindings() {
  HOME="$(mktemp -d)" ARCH_PATH="$ROOT" lua <<'LUA'
package.path = os.getenv("ARCH_PATH") .. "/?.lua;" .. package.path

local function proxy()
  return setmetatable({}, {
    __index = function(self, key)
      local value = proxy()
      rawset(self, key, value)
      return value
    end,
    __call = function()
      return {}
    end,
  })
end

local dsp = proxy()
rawset(dsp, "global", function(name) return { global = name } end)
rawset(dsp, "exec_cmd", function(command) return { exec = command } end)

hl = setmetatable({
  dsp = dsp,
  bind = function(keys, dispatcher, opts)
    local kind, target = "other", ""
    if type(dispatcher) == "table" and dispatcher.global then
      kind, target = "global", dispatcher.global
    elseif type(dispatcher) == "table" and dispatcher.exec then
      kind, target = "exec", dispatcher.exec
    end
    print(kind .. "\t" .. target .. "\t" .. ((opts or {}).description or ""))
  end,
}, {
  __index = function()
    return function() return {} end
  end,
})

require("default.hypr.helpers")

o.bind("A", "listed menu", { menu = "theme" })
o.bind("B", "unlisted menu", { menu = "setup.power" })
o.bind("C", "listed panel", { panel = "arch.emojis" })
o.bind("D", "unlisted panel", { panel = "arch.wifiqr" })
o.bind("E", "listed audio", { audio = "raise" })
o.bind("F", "unlisted audio", { audio = "+1" })
o.bind("I", "listed brightness", { brightness = "raise" })
o.bind("G", "listed ipc", { ipc = "media.next" })
o.bind("H", "unlisted ipc", { ipc = "media.sourceNext" })

for _, file in ipairs({ "utilities", "clipboard", "media" }) do
  dofile(os.getenv("ARCH_PATH") .. "/default/hypr/bindings/" .. file .. ".lua")
end
LUA
}

bindings=$(list_bindings)

expect_binding() {
  local expected="$1"
  local message="$2"
  grep -Fxq "$expected" <<<"$bindings" || fail "$message: $(grep -F "$(cut -f3 <<<"$expected")" <<<"$bindings")"
}

expect_binding $'exec\tarch-menu toggle \'theme\'\tlisted menu' "a listed menu route uses the shell IPC command"
expect_binding $'exec\tarch-menu toggle \'setup.power\'\tunlisted menu' "an unlisted menu route falls back to the command"
expect_binding $'exec\tarch-shell shell toggle \'arch.emojis\'\tlisted panel' "a listed panel uses the shell IPC command"
expect_binding $'exec\tarch-shell shell toggle \'arch.wifiqr\'\tunlisted panel' "an unlisted panel falls back to the command"
expect_binding $'exec\tarch-audio-output-volume \'raise\'\tlisted audio' "a listed volume key uses the audio command"
expect_binding $'exec\tarch-audio-output-volume \'+1\'\tunlisted audio' "an unlisted volume step falls back to the script"
expect_binding $'exec\tarch-brightness-display +5%\tlisted brightness' "a listed brightness key uses the display command"
expect_binding $'exec\tarch-shell \'media\' \'next\'\tlisted ipc' "a listed IPC call uses the shell command"
expect_binding $'exec\tarch-shell \'media\' \'sourceNext\'\tunlisted ipc' "an unlisted IPC call falls back to arch-shell"
pass "shell bindings use working shell IPC commands"

# Every default binding that toggles a menu or panel uses an IPC command the
# running shell can serve after it registers its plugin IDs.
expect_binding $'exec\tarch-menu toggle \'root\'\tMenu' "SUPER+SPACE opens the menu through shell IPC"
expect_binding $'exec\tarch-menu toggle \'theme\'\tTheme menu' "the theme menu uses shell IPC"
expect_binding $'exec\tarch-shell shell toggle \'arch.clipboard\'\tClipboard manager' "the clipboard binding uses shell IPC"
expect_binding $'exec\tarch-audio-output-volume \'raise\'\tVolume up' "the volume up key reaches the audio command"
expect_binding $'exec\tarch-audio-output-volume \'lower\'\tVolume down' "the volume down key reaches the audio command"
expect_binding $'exec\tarch-audio-output-volume \'mute-toggle\'\tMute' "the mute key reaches the audio command"
expect_binding $'exec\tarch-brightness-display +5%\tBrightness up' "the brightness up key reaches the display command"
expect_binding $'exec\tarch-brightness-display 5%-\tBrightness down' "the brightness down key reaches the display command"
expect_binding $'exec\tarch-shell \'media\' \'playPause\'\tPlay' "the play key reaches the media service through shell IPC"
expect_binding $'exec\tarch-shell \'notifications\' \'dismissOne\'\tDismiss last notification' "dismissing a notification reaches the service through IPC"
pass "default menu, panel, media, and notification bindings use shell IPC"

# The shell and the helpers read the same list, in the same format.
while IFS= read -r line; do
  [[ -z $line || $line == \#* ]] && continue
  [[ $line =~ ^(menu|panel|audio|brightness|ipc)\ [^[:space:]]+$ ]] || fail "shortcuts lines are a kind and a target: $line"
  if [[ $line == ipc\ * ]]; then
    [[ $line =~ ^ipc\ (media|notifications)\.[A-Za-z]+$ ]] || fail "ipc shortcuts name a mapped target and method: $line"
  fi
done <"$shortcuts"
grep -q 'path: shell.archPath + "/default/arch/shortcuts"' "$ROOT/src/arch/shell/shell.qml" ||
  fail "the shell registers the declared shortcuts"
! grep -q 'hl\.dsp\.global' "$ROOT/default/hypr/helpers.lua" ||
  fail "desktop keybindings do not pass unsupported D-Bus dispatchers to Hyprland"
# An ipc shortcut runs the service's own IPC handler, so it behaves exactly as
# the arch-shell call it replaces.
for service in services/media notifications; do
  grep -Pzq 'function runShortcut\(method\) \{\n    if \(typeof ipcHandler\[method\] !== "function"\) return false\n    ipcHandler\[method\]\(\)' "$ROOT/src/arch/shell/plugins/$service/Service.qml" ||
    fail "$service runs ipc shortcuts through its IPC handler"
  grep -Pzq '(IpcHandler|ShellIpc) \{\n    id: ipcHandler' "$ROOT/src/arch/shell/plugins/$service/Service.qml" ||
    fail "$service names its IPC handler for shortcuts"
done
pass "the shell and the helpers share one shortcut list"

# Every default menu binding target is a real menu route.
run_node_test <<'JS'
const fs = require('fs')
const menu = requireFromRoot('src/arch/shell/plugins/menu/MenuModel.js')
const entries = menu.parseMenuJsonc(fs.readFileSync(path.join(root, 'default/arch/arch-menu.jsonc'), 'utf8'))
const items = {}
const order = []
for (const entry of entries) { items[entry.id] = entry; order.push(entry.id) }
items.root = items.root || { id: 'root' }

const lines = fs.readFileSync(path.join(root, 'default/arch/shortcuts'), 'utf8').split('\n')
for (const line of lines) {
  const match = /^menu (\S+)$/.exec(line)
  if (!match) continue
  const route = match[1]
  assert(route === 'root' || items[menu.resolveRoute(items, order, route)], `shortcut menu route resolves: ${route}`)
}
JS
pass "every shortcut menu route resolves in the menu"
