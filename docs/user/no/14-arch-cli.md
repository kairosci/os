# Arch CLI

Arch styres vanligvis gjennom snarveiene og Arch-menyen (`Super + Space`). Men du kan også styre den gjennom `arch` CLI-et. Dette er særlig nyttig når du har en AI-agent som jobber med deg på tilpasning eller konfigurasjon.

CLI-et har tilgang til alt det interne verktøyet som brukes både via menyen og ellers. Du kan se alt som er tilgjengelig ved å kjøre `arch` i terminalen.

Det ser omtrent slik ut:

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

Og du kan gå dypere på hver gruppe:

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

Hver kommando tar også `--help`, enten du spør en hel gruppe (`archctl capture --help`) eller én enkelt kommando (`archctl capture screenshot --help`).

### Åpne menyen fra terminalen

Arch-menyen er også skriptbar, noe som er hendig for dine egne tastebindinger. `archctl menu` åpner den ved roten, og du kan hoppe rett til ethvert punkt i treet ved å navngi det: `archctl menu summon style.theme` går rett til temavelgeren, `archctl menu toggle system` åpner systemmenyen og lukker den igjen hvis den allerede er oppe, og `archctl menu close` legger den bort.
