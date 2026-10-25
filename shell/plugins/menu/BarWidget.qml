import Quickshell
import QtQuick
import qs.Ui

BarWidget {
  id: root
  moduleName: "arch.menu"

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    iconComponent: Component {
      Image {
        source: Quickshell.env("ARCH_PATH") + "/arch-mark.svg"
        width: 20
        height: 20
        fillMode: Image.PreserveAspectFit
        smooth: true
      }
    }
    onPressed: function(button) {
      if (!root.bar) return
      if (button === Qt.RightButton) root.bar.run("xdg-terminal-exec")
      else root.bar.run("arch-shell shell toggle arch.menu '{\"menu\":\"root\"}'")
    }
  }
}
