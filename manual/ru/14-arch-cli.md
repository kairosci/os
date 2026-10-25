# CLI Arch

Arch обычно управляется через сочетания клавиш и меню Arch (`Super + Space`). Но ей также можно управлять через CLI `arch`. Это особенно полезно, когда ИИ-агент работает с вами над настройкой или конфигурацией.

CLI имеет доступ ко всем внутренним инструментам, используемым как через меню, так и иным образом. Всё доступное можно увидеть, выполнив `arch` в терминале.

Это выглядит примерно так:

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

И можно углубиться в каждую группу:

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

Каждая команда также принимает `--help`, спрашиваете ли вы целую группу (`archctl capture --help`) или одну команду (`archctl capture screenshot --help`).

### Открытие меню из терминала

Меню Arch также поддаётся скриптингу, что удобно для ваших собственных привязок клавиш. `archctl menu` открывает его в корне, а вы можете перейти прямо к любой точке дерева, назвав её: `archctl menu summon style.theme` переходит прямо к выбору темы, `archctl menu toggle system` открывает системное меню и снова закрывает его, если оно уже открыто, а `archctl menu close` убирает его.
