import QtQuick
import qs.Ui

// A first-party Quickshell player. The lock service keeps a decoded poster
// underneath until the video frame is ready and pauses playback when covered.
Item {
  id: root

  property string mediaPath: ""
  property bool playbackEnabled: true

  BackgroundMedia {
    anchors.fill: parent
    path: root.mediaPath
    playbackEnabled: root.playbackEnabled
    audioEnabled: false
  }
}
