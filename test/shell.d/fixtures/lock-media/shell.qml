import QtQuick
import Quickshell

ShellRoot {
  id: root
  property var view
  property var wallpaper
  property var video
  property int step: 0

  Item { id: host; width: 1000; height: 700 }

  function findItem(item, name) {
    if (item.objectName === name) return item
    for (var i = 0; i < item.children.length; i++) {
      var found = findItem(item.children[i], name)
      if (found) return found
    }
    return null
  }

  function check(condition, message) {
    if (!condition) throw new Error(message)
  }

  Timer {
    interval: 150
    repeat: true
    running: true
    onTriggered: {
      try {
        if (root.step === 0) {
          var component = Qt.createComponent("file://" + Quickshell.env("ARCH_PATH") + "/shell/plugins/lock/LockView.qml")
          check(component.status === Component.Ready, component.errorString())
          root.view = component.createObject(host, {width: 1000, height: 700, backgroundPath: "/still.png", loadBackground: false})
          check(root.view !== null, component.errorString())
          root.wallpaper = findItem(root.view, "lockWallpaper")
          root.video = findItem(root.view, "lockVideoLoader")
          check(root.wallpaper.path === "", "hidden still must not decode")
          root.view.backgroundPath = "/video.mp4"
          root.view.videoPosterPath = "/poster.jpg"
        } else if (root.step === 1) {
          check(!root.video.active && root.video.item === null, "hidden video does not create a player")
          root.view.loadBackground = true
          root.view.powerSaverActive = true
        } else if (root.step === 2) {
          check(root.wallpaper.path === "/poster.jpg", "power saver keeps the video poster")
          check(!root.video.active, "power saver pauses and releases the player")
          root.view.powerSaverActive = false
        } else if (root.step === 3) {
          check(root.video.active && root.video.item !== null, "visible video loads the native player")
          check(root.video.item.mediaPath === "/video.mp4", "native player receives the selected video")
          check(root.wallpaper.path === "/poster.jpg", "poster stays beneath the feed before its first frame")
          root.view.displaysBlank = true
        } else if (root.step === 4) {
          check(!root.video.active && root.video.item === null, "blanking releases the player")
          root.view.loadBackground = false
        } else {
          check(root.wallpaper.path === "", "unlock releases the poster image")
          console.log("LOCK_MEDIA_TEST_PASS")
          Qt.quit()
        }
        root.step++
      } catch (error) {
        console.error("LOCK_MEDIA_TEST_FAIL: " + error)
        Qt.quit()
      }
    }
  }
}
