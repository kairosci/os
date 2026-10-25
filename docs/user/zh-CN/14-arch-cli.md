# Arch CLI

Arch 通常通过快捷键和 Arch 菜单（`Super + Space`）来控制。但你也可以通过 `arch` CLI 来控制它。当你让 AI 智能体与你一起进行自定义或配置时，这尤其有帮助。

CLI 可以访问通过菜单和其他方式使用的所有内部工具。你可以在终端中运行 `arch` 查看所有可用内容。

它看起来像这样：

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

你可以深入了解每个组：

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

每个命令也都接受 `--help`，无论你是询问整个组（`archctl capture --help`）还是单个命令（`archctl capture screenshot --help`）。

### 从终端打开菜单

Arch 菜单也可以脚本化，这对于你自己的键盘绑定很方便。`archctl menu` 在根处打开它，你可以通过命名直接跳转到树中的任意点：`archctl menu summon style.theme` 直接转到主题选择器，`archctl menu toggle system` 打开系统菜单，如果它已经打开则再次关闭它，`archctl menu close` 将其收起。
