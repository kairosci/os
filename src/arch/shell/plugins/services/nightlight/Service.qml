import QtQuick
import Quickshell.Io
import "NightlightModel.js" as NightlightModel
import qs.Commons

Item {
  id: root

  // Injected by arch-shell (the first-party service loader).
  property var shell: null

  property bool stateLoaded: false
  property var status: ({ enabled: false, temperature: null })
  readonly property bool enabled: stateLoaded && status !== null && status.enabled

  property bool hasPendingState: false
  property bool pendingEnabled: false

  function refresh() {
    if (!statusProbe.running) statusProbe.running = true
  }

  function setNightlight(value) {
    applyState(value)
  }

  function toggle() {
    setNightlight(!enabled)
  }

  function applyState(value) {
    if (applyProcess.running) {
      root.pendingEnabled = value
      root.hasPendingState = true
      return
    }

    runApply(value)
  }

  function runApply(value) {
    applyProcess.command = ["archctl", "toggle", "nightlight", value ? "on" : "off"]
    applyProcess.running = true
  }

  Process {
    id: statusProbe
    command: ["archctl", "toggle", "nightlight", "--status"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        var parsed = NightlightModel.statusFromOutput(text)
        root.status = parsed === null ? { enabled: false, temperature: null } : parsed
        root.stateLoaded = true
      }
    }
    onExited: function(exitCode) {
      if (exitCode !== 0) {
        root.status = { enabled: false, temperature: null }
        root.stateLoaded = true
      }
    }
  }

  Process {
    id: applyProcess
    onExited: function() {
      if (root.hasPendingState) {
        root.hasPendingState = false
        root.runApply(root.pendingEnabled)
        return
      }

      root.refresh()
    }
  }

  Component.onCompleted: refresh()

  ShellIpc {
    target: "nightlight"

    function status(): string {
      return JSON.stringify(root.status)
    }

    function refresh(): void {
      root.refresh()
    }

    function enable(): string {
      root.setNightlight(true)
      return "enabled"
    }

    function disable(): string {
      root.setNightlight(false)
      return "disabled"
    }

    function toggle(): string {
      var enabling = !root.enabled
      root.setNightlight(enabling)
      return enabling ? "enabled" : "disabled"
    }
  }
}
