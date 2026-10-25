# Arch CLI

Arch зазвичай керують через гарячі клавіші й меню Arch (`Super + Space`). Але ви також можете керувати ним через CLI `arch`. Це особливо корисно, коли AI-агент працює з вами над налаштуванням або конфігурацією.

CLI має доступ до всіх внутрішніх інструментів, які використовуються як через меню, так і в інших місцях. Ви можете побачити все доступне, запустивши `arch` в терміналі.

Це виглядає приблизно так:

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

І ви можете зануритися глибше в кожну групу:

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

Кожна команда також приймає `--help`, чи питаєте ви цілу групу (`archctl capture --help`), чи одну команду (`archctl capture screenshot --help`).

### Відкриття меню з терміналу

Меню Arch також можна скриптувати, що зручно для ваших власних сполучень клавіш. `archctl menu` відкриває його в корені, а ви можете стрибнути просто до будь-якої точки дерева, назвавши її: `archctl menu summon style.theme` переходить просто до вибору теми, `archctl menu toggle system` відкриває системне меню й закриває його знову, якщо воно вже відкрите, а `archctl menu close` прибирає його.
