#!/bin/bash

set -euo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

run_node_test <<'JS'
const fs = require('fs')
const read = name => fs.readFileSync(path.join(root, name), 'utf8')
const model = requireFromRoot('src/arch/shell/plugins/services/remote-session/RemoteSessionModel.js')

assert(model.isCaptureEvent('screencast'), 'the screencast event triggers a probe')
assert(!model.isCaptureEvent('screencastv2'), 'the paired screencastv2 event does not double the probe')
assert(!model.isCaptureEvent('openwindow') && !model.isCaptureEvent(''), 'unrelated Hyprland events are ignored')

assertDeepEqual(model.stateFromOutput(''), { active: false, peers: [] }, 'no gliff-server means no session')
assertDeepEqual(model.stateFromOutput('\n'), { active: false, peers: [] }, 'blank output means no session')
assertDeepEqual(model.stateFromOutput('4321 \n'), { active: true, peers: [] }, 'a local server without ssh is a session with no known peer')
assertDeepEqual(model.stateFromOutput('4321 10.0.0.5\n'), { active: true, peers: ['10.0.0.5'] }, 'an ssh-spawned server reports the client address')
assertDeepEqual(model.stateFromOutput('1 10.0.0.5\n2 10.0.0.5\n3 fd00::9\n'), { active: true, peers: ['10.0.0.5', 'fd00::9'] }, 'peers are listed once each')

const service = read('src/arch/shell/plugins/services/remote-session/Service.qml')
const manifest = JSON.parse(read('src/arch/shell/plugins/services/remote-session/manifest.json'))
assertEqual(manifest.id, 'arch.remote-session', 'service manifest id matches the indicator lookup')
assert(manifest.kinds.includes('service') && manifest.entryPoints.service === 'Service.qml', 'service manifest declares a service entry point')
assert(service.includes('target: Hyprland') && service.includes('isCaptureEvent(event ? event.name : "")'), 'service re-probes on Hyprland screencast events')
assert(service.includes('eventDebounce.restart()'), 'service debounces event bursts into one probe')
assert(service.includes('/src/arch/shell/plugins/services/remote-session/probe.py"'), 'service runs the shared Python probe')
assert(service.includes('running: root.active') && service.includes('interval: 2000'), 'service polls only while a session is active, since the stop event is not reliable')
assert(!service.includes('archctl notification send'), 'a session is shown by the indicator alone, with no notification')

const indicator = read('src/arch/shell/plugins/bar/indicators/RemoteSession.qml')
const widget = read('src/arch/shell/plugins/bar/widgets/Indicators.qml')
const widgetManifest = JSON.parse(read('src/arch/shell/plugins/bar/widgets/Indicators.manifest.json'))
assert(widget.match(/defaultIndicatorEntries: \[ "ScreenRecording", "RemoteSession"/), 'remote session is included in the default indicator tray')
assert(widgetManifest.barWidget.schema.find(field => field.key === 'items').options.some(option => option.value === 'RemoteSession'), 'remote session is configurable alongside the other indicators')
assert(indicator.includes('firstPartyServiceFor("arch.remote-session")'), 'indicator reads the remote session service')
assert(indicator.includes('Commons.I18n.t("bar.remoteSessionFrom").arg(peers.join(", "))'), 'active tooltip names the connected peers')
assert(indicator.includes('useActiveColor: true') && indicator.includes('activeColor: Commons.Color.urgent'), 'active remote session uses the theme danger color')
assert(indicator.includes('revealWhenInactive: false'), 'remote session shows only while a session is active, not among the inactive indicators a hover reveals')
const barIndicator = fs.readFileSync(path.join(root, 'src/arch/shell/Ui/BarIndicator.qml'), 'utf8')
assert(
  /belongsInBlock:[^\n]*indicatorBlock === "inactive" \? !effectiveActive && revealWhenInactive/.test(barIndicator)
    && /inactiveRevealed: !effectiveActive && revealWhenInactive &&/.test(barIndicator),
  'an indicator that opts out is neither placed nor revealed among the inactive ones'
)
assert(!indicator.includes('visible:'), 'remote session uses the shared indicator visibility and hover behavior')
assert(indicator.includes('root.remoteSessionService.refresh()'), 'indicator refresh re-probes the service')

const shell = read('src/arch/shell/shell.qml')
assert((shell.match(/"arch\.remote-session"/g) || []).length >= 2, 'third-party bar clones can read the remote session service')
const api = read('src/arch/shell/services/PluginFirstPartyServiceApi.qml')
assert(api.includes('property bool active: false') && api.includes('property var peers: []'), 'service proxy exposes the remote session state')
assert(api.includes('serviceId === "arch.remote-session" && _refresh') && shell.includes('_refresh: function()'), 'service proxy forwards refresh for cloned indicator widgets')
JS

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
mkdir -p "$TMPDIR/bin" "$TMPDIR/proc/100" "$TMPDIR/proc/200" "$TMPDIR/proc/300"

probe_script="$ROOT/src/arch/shell/plugins/services/remote-session/probe.py"
cat >"$TMPDIR/bin/pgrep" <<'SH'
#!/bin/bash
[[ $1 == "-x" && $2 == "-u" && $3 == "$(id -u)" && $4 == "gliff-server" ]] || exit 2
[[ -n ${GLIFF_PIDS:-} ]] || exit 1
printf '%s\n' $GLIFF_PIDS
SH
chmod +x "$TMPDIR/bin/pgrep"

probe() {
  PATH="$TMPDIR/bin:$PATH" GLIFF_PIDS="${1:-}" AP="$ROOT" \
    ARCH_PROC_ROOT="$TMPDIR/proc" "$probe_script"
}

[[ -z $(probe) ]] || fail "probe prints nothing without a gliff server"
pass "probe prints nothing without a gliff server"

printf 'gliff-server\n' >"$TMPDIR/proc/100/comm"
printf 'gliff-server\n' >"$TMPDIR/proc/200/comm"
printf 'other-process\n' >"$TMPDIR/proc/300/comm"
printf 'HOME=/home/x\0SSH_CONNECTION=10.0.0.5 51234 10.0.0.1 22\0TERM=foot\0' >"$TMPDIR/proc/100/environ"
printf 'HOME=/home/x\0TERM=foot\0' >"$TMPDIR/proc/200/environ"
printf 'SSH_CONNECTION=192.0.2.1 51234 10.0.0.1 22\0' >"$TMPDIR/proc/300/environ"

[[ $(probe "100 200 300") == $'100 10.0.0.5\n200 ' ]] || fail "probe reports owned server processes and ssh client addresses" "$(probe "100 200 300")"
pass "probe reports the ssh client address of a spawned server"

[[ $(probe "100 200 300" | wc -l) == 2 ]] || fail "probe lists only matching server processes"
pass "probe lists only matching server processes"

mkdir -p "$TMPDIR/invalid/data/shell"
printf '%s\n' 'commands: [' >"$TMPDIR/invalid/data/shell/remote-session.yml"
set +e
AP="$TMPDIR/invalid" "$probe_script" >"$TMPDIR/invalid-output" 2>"$TMPDIR/invalid-error"
config_status=$?
set -e
(( config_status == 78 )) || fail "remote-session probe reports malformed settings at its command boundary"
grep -Fq 'Could not load remote-session configuration' "$TMPDIR/invalid-error" ||
  fail "remote-session probe explains malformed settings"
! grep -Fq 'Traceback' "$TMPDIR/invalid-error" || fail "remote-session probe does not leak a traceback"
pass "remote-session probe handles malformed YAML at its command boundary"
