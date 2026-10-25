# Arch CLI

Arch se obično kontrolira prečacima i Arch izbornikom (`Super + Space`). Ali možete ga kontrolirati i putem CLI-ja `arch`. To je osobito korisno kada vam AI agent pomaže u prilagodbi ili konfiguraciji.

CLI ima pristup svim internim alatima koji se koriste i putem izbornika i na drugi način. Sve što je dostupno možete vidjeti pokretanjem `arch` u terminalu.

Izgleda otprilike ovako:

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

I možete kopati dublje po svakoj grupi:

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

Svaka naredba također prima `--help`, bilo da pitate cijelu grupu (`archctl capture --help`) ili jednu naredbu (`archctl capture screenshot --help`).

### Otvaranje izbornika iz terminala

Arch izbornik također se može skriptirati, što je zgodno za vaše vlastite poveznice tipki. `archctl menu` otvara ga u korijenu, a izravno možete skočiti na bilo koju točku u stablu imenovanjem: `archctl menu summon style.theme` ide ravno na birač tema, `archctl menu toggle system` otvara izbornik sustava i ponovno ga zatvara ako je već otvoren, a `archctl menu close` ga sprema.
