# Arch CLI

Arch は通常、ホットキーと Arch メニュー（`Super + Space`）から制御します。しかし `arch` CLI からも制御できます。これは、AI エージェントにカスタマイズや設定を一緒にやってもらうときに特に役立ちます。

CLI は、メニュー経由やそれ以外で使われるすべての内部ツールにアクセスできます。ターミナルで `arch` を実行すると、利用可能なもののすべてが見えます。

こんな感じです：

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

そしてすべてのグループをより深く掘り下げることもできます：

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

すべてのコマンドは `--help` も受け付けます。グループ全体でも（`archctl capture --help`）、単一のコマンドでも（`archctl capture screenshot --help`）です。

### ターミナルからメニューを開く

Arch メニューはスクリプト化もでき、自分のキーバインドに便利です。`archctl menu` はルートで開き、名前を指定するとツリーの任意のポイントへ直接ジャンプできます：`archctl menu summon style.theme` はテーマピッカーへ直接行き、`archctl menu toggle system` はシステムメニューを開き、すでに開いていれば再び閉じ、`archctl menu close` は片付けます。
