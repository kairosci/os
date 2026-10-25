# Arch CLI

Arch 通常透過快捷鍵和 Arch 選單（`Super + Space`）來控制。但你也可以透過 `arch` CLI 來控制它。當你讓 AI 代理程式和你一起處理自訂或設定時，這特別有幫助。

這個 CLI 可以存取所有透過選單以及其他方式使用的內部工具。在終端機中執行 `arch`，你就可以看到所有可用的東西。

它看起來像這樣：

```
~ ❯ arch
Arch command center

Usage:
  archctl <command> [args...]
  archctl commands [--all] [--json] [--check]
  archctl <group> --help
  archctl <group> <command> --help

Common commands:
  archctl update              Update Arch and system packages
  archctl theme list          List available themes
  archctl theme set <name>    Apply a theme
  archctl font list           List available fonts
  archctl screenshot          Take a screenshot
  archctl debug               Print debugging information

Groups:
  agent          AI coding agents, their usage, and subscription accounts
  audio          Audio input and output controls
  bar            Arch shell bar layout and settings
  battery        Battery status helpers
  bluetooth      Bluetooth device controls
  branch         Arch git branch management
  branding       About and screensaver branding
  brightness     Display and keyboard brightness
  capture        Screenshots and screen recording
  channel        Arch release channel management
  clipboard      Clipboard helpers
  cmd            Command and shortcut helpers
  config         System configuration helpers
  debug          Diagnostics and support logs
  ...
```

而你可以深入每一個群組：

```
~ ❯ archctl capture
Capture commands — Screenshots and screen recording:
  archctl capture qr                                                                                                                                                                                                       Decode a QR code from a screenshot region
  archctl capture screenrecording [--fullscreen] [--with-desktop-audio] [--with-microphone-audio] [--with-webcam] [--webcam-device=<device>] [--webcam-size=<small|medium|large>] [--resolution=<size>] [--stop-recording]  Start or stop screen recording
  archctl capture screenrecording with webcam                                                                                                                                                                              Pick a webcam and start a screen recording with it
  archctl capture screenshot [smart|region|windows|fullscreen|scroll] [copy|save]                                                                                                                                          Take a screenshot
  archctl capture text                                                                                                                                                                                                     Extract text from a screenshot region with OCR
  archctl capture webcam resize <smaller|larger|reset|small|medium|large>                                                                                                                                                  Resize the active webcam recording overlay
```

每一個指令也都接受 `--help`，無論你問的是一整個群組（`archctl capture --help`）還是單一個指令（`archctl capture screenshot --help`）。

### 從終端機開啟選單

Arch 選單也可以用腳本控制，這對你自己的快捷鍵很有用。`archctl menu` 會在根目錄開啟它，而你可以透過命名直接跳到樹狀結構中的任何一點：`archctl menu summon style.theme` 會直接前往主題選擇器，`archctl menu toggle system` 會開啟系統選單，若它已經開啟則再次關閉，而 `archctl menu close` 會把它收起來。
