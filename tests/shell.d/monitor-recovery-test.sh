#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

monitor_watch="$ROOT/src/arch/commands/arch-hyprland-monitor-watch"
monitor_internal="$ROOT/src/arch/commands/arch-hyprland-monitor-internal"
monitor_mirror="$ROOT/src/arch/commands/arch-hyprland-monitor-internal-mirror"
monitor_laptop="$ARCH_TEST_CLI_BIN/arch-hyprland-monitor-laptop"
system_wake="$ROOT/src/arch/commands/arch-system-wake"
clamshell="$ROOT/src/arch/commands/arch-hyprland-monitor-clamshell"
lock_service="$ROOT/src/arch/shell/plugins/lock/Service.qml"
hw_clamshell="$ROOT/src/arch/commands/arch-hw-clamshell"
hw_laptop_closed="$ROOT/src/arch/commands/arch-hw-laptop-closed"
utilities="$ROOT/default/hypr/bindings/utilities.lua"

grep -F 'sleep "$delay"' "$monitor_watch" >/dev/null
grep -F 'for delay in 1 3 7; do' "$monitor_watch" >/dev/null
grep -F 'poll_clamshell_state &' "$monitor_watch" >/dev/null
grep -F 'flock -n 9' "$monitor_watch" >/dev/null
grep -F 'arch-hyprland-monitor-clamshell' "$monitor_watch" >/dev/null
pass "monitor watcher retries internal monitor recovery after removal"

grep -F 'monitoradded\>\>*|monitoraddedv2\>\>*)' "$monitor_watch" >/dev/null
grep -F 'arch-hyprland-monitor-clamshell' "$monitor_watch" >/dev/null
pass "monitor watcher disables the internal monitor after closed-lid external hotplug"

grep -F 'sync_clamshell_after_monitor_change' "$monitor_watch" >/dev/null
grep -F 'socat -U - "UNIX-CONNECT:$SOCKET"' "$monitor_watch" >/dev/null
pass "monitor watcher reconciles clamshell state on startup"

grep -F 'arch-hw-laptop && arch-hyprland-monitor-external-active' "$monitor_watch" >/dev/null
grep -F 'sync_poll_state' "$monitor_watch" >/dev/null
grep -F 'done < <(socat' "$monitor_watch" >/dev/null
pass "clamshell poll only runs on a docked laptop, not desktops or undocked laptops"

# Recovery costs a reload per attempt, so it must not run on a healthy machine,
# and only one loop may run across the events that start it.
grep -F '(( state == 1 )) && break' "$monitor_watch" >/dev/null
grep -F 'delay = delay * 2 > 60 ? 60 : delay * 2' "$monitor_watch" >/dev/null
grep -F '9>"$MODELESS_LOCK"' "$monitor_watch" >/dev/null
grep -F 'flock -w 1 9 || exit 0' "$monitor_watch" >/dev/null
pass "modeless monitor recovery runs one backing-off loop while a monitor has no mode"

# Nothing fires an event for this state, so an unanswered query must not end
# recovery -- but a compositor that never answers has gone with the session.
grep -F '(( state == 2 )) && (( ++unanswered > 20 )) && break' "$monitor_watch" >/dev/null
pass "modeless recovery retries unanswered queries without waiting on a dead compositor"

grep -F 'configreloaded\>\>*)' "$monitor_watch" >/dev/null
pass "modeless recovery also runs after a config reload"

grep -F 'arch-hyprland-reload-guard paused' "$monitor_watch" >/dev/null
pass "modeless recovery does not reload into a package transaction"

grep -F 'arch-hw-laptop-closed && arch-hw-external-monitors' "$hw_clamshell" >/dev/null
grep -F 'org.freedesktop.login1.Manager LidClosed' "$hw_laptop_closed" >/dev/null
grep -F 'ARCH_ACPI_LID_PATH:-/proc/acpi/button/lid' "$hw_laptop_closed" >/dev/null
pass "clamshell helper detects closed-lid external monitor state"

# A mirrored external is absent from plain `monitors`, so asking without `all`
# reads as a disconnect and hands the mirror toggle straight to recovery.
grep -F 'arch-hyprland-monitor-internal recover >/dev/null 2>&1 || true' "$clamshell" >/dev/null
grep -F 'arch-hyprland-monitor-internal-mirror recover >/dev/null 2>&1 || true' "$clamshell" >/dev/null
grep -F 'internal-monitor-clamshell.lua' "$clamshell" >/dev/null
grep -F 'disabled = true' "$clamshell" >/dev/null
grep -F 'MANUAL_DISABLE_FLAG' "$clamshell" >/dev/null
! grep -F 'rm -f "$MANUAL_DISABLE_FLAG"' "$clamshell" >/dev/null
! grep -F '>"$MANUAL_DISABLE_FLAG"' "$clamshell" >/dev/null
grep -F 'read_monitor_scale' "$clamshell" >/dev/null
grep -F 'scale = $scale' "$clamshell" >/dev/null
grep -F 'hyprctl dispatch "hl.dsp.dpms({ action = \"$action\", monitor = \"$INTERNAL\" })"' "$clamshell" >/dev/null
grep -F 'hyprctl monitors all -j' "$clamshell" >/dev/null
grep -F 'arch-hyprland-monitor-external-active' "$clamshell" >/dev/null
grep -F 'arch-hw-clamshell' "$clamshell" >/dev/null
pass "clamshell monitor sync disables laptop output and force-recovers it"

grep -F "hyprctl dispatch 'hl.dsp.dpms({ action = \"enable\" })' >/dev/null 2>&1 || true" "$monitor_internal" >/dev/null
grep -F 'arch-hyprland-monitor-laptop' "$monitor_internal" >/dev/null
grep -F 'hyprctl monitors all -j' "$monitor_laptop" >/dev/null
grep -F 'arch-hyprland-monitor-external-active' "$monitor_internal" >/dev/null
grep -F 'wake' "$monitor_internal" >/dev/null
grep -F 'arch-hyprland-toggle-enabled $TOGGLE || return 0' "$monitor_internal" >/dev/null
pass "internal monitor helper can re-enable disabled laptop displays"
pass "internal monitor recovery only wakes displays when it re-enables one"

grep -F 'arch-hyprland-monitor-external-active' "$monitor_mirror" >/dev/null
pass "internal mirror helper recovers when no active external display remains"

grep -F 'switch:on:Lid Switch", nil, "arch-system-lid-close"' "$utilities" >/dev/null
grep -F 'switch:off:Lid Switch", nil, "arch-hyprland-monitor-clamshell"' "$utilities" >/dev/null
grep -F 'switch:on:Apple SMC power/lid events", nil, "arch-system-lid-close"' "$utilities" >/dev/null ||
  fail "closing an Apple Silicon lid runs the same lid-close as any laptop"
grep -F 'switch:off:Apple SMC power/lid events", nil, "arch-hyprland-monitor-clamshell"' "$utilities" >/dev/null ||
  fail "opening an Apple Silicon lid restores the panel like any laptop"
pass "lid switch bindings lock on close and reconcile clamshell display state"

grep -F 'arch-hyprland-monitor-clamshell >/dev/null 2>&1 || true' "$system_wake" >/dev/null
pass "system wake resyncs clamshell display state"

grep -F 'lock-pending: no-real-screen' "$lock_service" >/dev/null
grep -F 'lock-pending: screen-stabilizing' "$lock_service" >/dev/null
grep -F 'id: sessionLockStabilizeTimer' "$lock_service" >/dev/null
grep -Pzo 'function onScreensChanged\(\) \{\n(.*\n)*?\s*root\.requestSessionLock\(\)\n' "$lock_service" >/dev/null
grep -F 'realScreens: root.realScreenCount()' "$lock_service" >/dev/null
pass "lock service waits for stable real screens before session lock"
