# Arch CLI

Arch sa zvyčajne ovláda cez klávesové skratky a menu Arch (`Super + Space`). Ale môžete ho ovládať aj cez `arch` CLI. To je obzvlášť užitočné, keď s vami AI agent pracuje na prispôsobení alebo konfigurácii.

CLI má prístup ku všetkým interným nástrojom, ktoré sa používajú cez menu aj inak. Všetko, čo je k dispozícii, uvidíte spustením `arch` v termináli.

Vyzerá to asi takto:

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

A môžete sa ponoriť hlbšie do každej skupiny:

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

Každý príkaz tiež prijíma `--help`, či už sa pýtate celej skupiny (`archctl capture --help`) alebo jedného príkazu (`archctl capture screenshot --help`).

### Otvorenie menu z terminálu

Menu Arch je tiež skriptovateľné, čo je šikovné pre vaše vlastné klávesové väzby. `archctl menu` ho otvára v koreni a môžete skočiť priamo do ktoréhokoľvek bodu v strome tým, že ho pomenujete: `archctl menu summon style.theme` ide priamo na výber tém, `archctl menu toggle system` otvára systémové menu a znova ho zatvorí, ak je už otvorené, a `archctl menu close` ho odloží.
