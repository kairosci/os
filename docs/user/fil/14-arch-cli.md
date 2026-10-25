# Arch CLI

Karaniwang kinokontrol ang Arch sa pamamagitan ng mga hotkey at ng menu ng Arch (`Super + Space`). Ngunit maaari mo rin itong kontrolin sa pamamagitan ng `arch` CLI. Partikular itong nakakatulong kapag mayroon kang isang AI agent na nakikipagtulungan sa iyo sa pag-customize o configuration.

Ang CLI ay may access sa lahat ng internal tooling na ginagamit parehong sa pamamagitan ng menu at kung hindi man. Makikita mo ang lahat ng available sa pamamagitan ng pagpapatakbo ng `arch` sa terminal.

Mukha itong ganito:

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

At maaari kang sumisid nang mas malalim sa bawat grupo:

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

Tumatanggap din ang bawat command ng `--help`, magtanong ka man sa isang buong grupo (`archctl capture --help`) o sa isang nag-iisang command (`archctl capture screenshot --help`).

### Pagbubukas ng menu mula sa terminal

Ang menu ng Arch ay scriptable din, na madaling gamitin para sa sarili mong mga keybinding. Binubuksan ito ng `archctl menu` sa root, at maaari kang tumalon nang diretso sa anumang punto sa tree sa pamamagitan ng pagpapangalan dito: ang `archctl menu summon style.theme` ay dumidiretso sa tagapili ng tema, ang `archctl menu toggle system` ay binubuksan ang menu ng sistema at isinasara ito ulit kung nakataas na ito, at ang `archctl menu close` ay inaalis ito.
