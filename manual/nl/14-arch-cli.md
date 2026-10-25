# Arch CLI

Arch wordt meestal bediend via de sneltoetsen en het Arch-menu (`Super + Space`). Maar je kunt het ook bedienen via de `arch` CLI. Dit is bijzonder handig wanneer je een AI-agent met je laat werken aan aanpassing of configuratie.

De CLI heeft toegang tot alle interne tooling die zowel via het menu als anderszins wordt gebruikt. Je kunt alles zien wat beschikbaar is door `arch` uit te voeren in de terminal.

Het ziet er ongeveer zo uit:

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

En je kunt dieper duiken in elke groep:

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

Elk commando accepteert ook `--help`, of je nu een hele groep vraagt (`archctl capture --help`) of een enkel commando (`archctl capture screenshot --help`).

### Het menu openen vanaf de terminal

Het Arch-menu is ook scriptbaar, wat handig is voor je eigen keybindings. `archctl menu` opent het bij de root, en je kunt rechtstreeks naar elk punt in de boom springen door het te benoemen: `archctl menu summon style.theme` gaat direct naar de themakiezer, `archctl menu toggle system` opent het systeemmenu en sluit het weer als het al open is, en `archctl menu close` bergt het op.
