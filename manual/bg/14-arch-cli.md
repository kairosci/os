# Arch CLI

Arch обикновено се управлява чрез клавишните комбинации и менюто на Arch (`Super + Space`). Но можеш да го управляваш и чрез CLI-то `arch`. Това е особено полезно, когато AI агент работи с теб върху персонализиране или конфигурация.

CLI-то има достъп до всички вътрешни инструменти, които се използват както чрез менюто, така и иначе. Можеш да видиш всичко налично, като изпълниш `arch` в терминала.

Изглежда нещо подобно:

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

И можеш да навлезеш по-дълбоко във всяка група:

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

Всяка команда също приема `--help`, независимо дали питаш цяла група (`archctl capture --help`) или единична команда (`archctl capture screenshot --help`).

### Отваряне на менюто от терминала

Менюто на Arch също може да се скриптира, което е удобно за собствените ти клавишни комбинации. `archctl menu` го отваря в корена и можеш да скочиш директно до всяка точка в дървото, като я назовеш: `archctl menu summon style.theme` отива директно на селектора за теми, `archctl menu toggle system` отваря системното меню и го затваря отново, ако вече е отворено, а `archctl menu close` го прибира.
