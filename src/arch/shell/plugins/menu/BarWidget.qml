import Quickshell
import Quickshell.Hyprland
import QtQuick
import qs.Commons
import qs.Commons as Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "arch.menu"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight
  readonly property var monitor: {
    var window = root.QsWindow.window
    var screen = window ? window.screen : null
    return screen ? Hyprland.monitorFor(screen) : Hyprland.focusedMonitor
  }
  property int workspaceRevision: 0

  function activeWorkspaceId() {
    var revision = root.workspaceRevision
    var monitorName = root.monitor ? String(root.monitor.name || "") : ""
    var workspaces = Hyprland.workspaces.values
    for (var i = 0; i < workspaces.length; i++) {
      var workspace = workspaces[i]
      if (workspace.active && workspace.monitor && workspace.monitor.name === monitorName)
        return workspace.id
    }
    return root.monitor && root.monitor.activeWorkspace ? root.monitor.activeWorkspace.id : 0
  }

  readonly property int workspaceNumber: root.activeWorkspaceId()


  Connections {
    target: Hyprland
    function onRawEvent(event) {
      var name = event ? String(event.name) : ""
      if (name === "workspacev2" || name === "focusedmonv2" || name === "moveworkspacev2" || name === "changeworkspaceid") {
        Hyprland.refreshMonitors()
        Hyprland.refreshWorkspaces()
        root.workspaceRevision++
      }
    }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    iconComponent: Component {
      Item {
        implicitWidth: 28
        implicitHeight: 28

        Image {
          anchors.fill: parent
          source: Quickshell.env("AP") + "/assets/branding/arch-mark.svg"
          fillMode: Image.PreserveAspectFit
          smooth: true
        }

        Rectangle {
          anchors.right: parent.right
          anchors.bottom: parent.bottom
          width: Math.max(16, workspaceNumberLabel.implicitWidth + 6)
          height: 16
          radius: height / 2
          color: Commons.Color.accent
          border.color: Commons.Color.bar.text
          border.width: 1
          visible: root.workspaceNumber > 0

          Text {
            id: workspaceNumberLabel
            anchors.centerIn: parent
            text: root.workspaceNumber > 0 ? String(root.workspaceNumber) : ""
            color: Commons.Color.bar.text
            font.family: Style.font.family
            font.pixelSize: Style.font.bodySmall
            font.bold: true
          }
        }
      }
    }
    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.run("xdg-terminal-exec")
      else root.bar.run("arch-shell shell toggle arch.menu '{\"menu\":\"root\"}'")
    }
  }
}
