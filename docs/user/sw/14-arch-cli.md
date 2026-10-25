# CLI ya Arch

Arch kwa kawaida hudhibitiwa kupitia mikato ya vitufe na menyu ya Arch (`Super + Space`). Lakini unaweza pia kuidhibiti kupitia CLI ya `arch`. Hii inasaidia hasa unapokuwa na ajenti wa AI anayefanya kazi nawe katika kubinafsisha au kusanidi.

CLI ina ufikiaji wa zana zote za ndani zinazotumiwa kupitia menyu na vinginevyo. Unaweza kuona kila kinachopatikana kwa kuendesha `arch` katika terminali.

Inaonekana kama hivi:

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

Na unaweza kuchimba zaidi katika kila kundi:

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

Kila amri huchukua `--help` pia, iwe unauliza kundi zima (`archctl capture --help`) au amri moja (`archctl capture screenshot --help`).

### Kufungua menyu kutoka terminali

Menyu ya Arch inaweza pia kuandikwa kwa hati, ambayo ni muhimu kwa mikato yako mwenyewe ya vitufe. `archctl menu` huifungua kwenye mzizi, na unaweza kuruka moja kwa moja hadi hatua yoyote katika mti kwa kuitaja: `archctl menu summon style.theme` huenda moja kwa moja hadi kichaguzi cha mandhari, `archctl menu toggle system` hufungua menyu ya mfumo na kuifunga tena ikiwa tayari iko wazi, na `archctl menu close` huiweka mbali.
