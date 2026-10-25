# CLI Arch

Arch se obvykle ovládá klávesovými zkratkami a nabídkou Arch (`Super + Space`). Můžete ho ale ovládat také prostřednictvím CLI `arch`. To je obzvlášť užitečné, když s vámi na přizpůsobení nebo konfiguraci pracuje AI agent.

CLI má přístup ke všem interním nástrojům, které se používají jak přes nabídku, tak jinak. Vše, co je k dispozici, uvidíte spuštěním `arch` v terminálu.

Vypadá to asi takto:

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

A u každé skupiny se můžete ponořit hlouběji:

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

Každý příkaz přijímá také `--help`, ať už se ptáte celé skupiny (`archctl capture --help`) nebo jednotlivého příkazu (`archctl capture screenshot --help`).

### Otevření nabídky z terminálu

Nabídka Arch je také skriptovatelná, což se hodí pro vaše vlastní klávesové zkratky. `archctl menu` ji otevře v kořenu a můžete skočit přímo na libovolný bod ve stromu jeho pojmenováním: `archctl menu summon style.theme` jde přímo do výběru motivu, `archctl menu toggle system` otevře systémovou nabídku a zase ji zavře, pokud už je nahoře, a `archctl menu close` ji uklidí.
