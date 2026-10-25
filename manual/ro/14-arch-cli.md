# CLI-ul Arch

Arch este controlat de obicei prin scurtături și meniul Arch (`Super + Space`). Dar îl poți controla și prin CLI-ul `arch`. Este deosebit de util atunci când ai un agent AI care lucrează cu tine la personalizare sau configurare.

CLI-ul are acces la toate instrumentele interne folosite atât prin meniu, cât și altfel. Poți vedea tot ce este disponibil rulând `arch` în terminal.

Arată cam așa:

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

Și poți aprofunda fiecare grup:

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

Fiecare comandă acceptă și `--help`, fie că întrebi un întreg grup (`archctl capture --help`), fie o singură comandă (`archctl capture screenshot --help`).

### Deschiderea meniului din terminal

Meniul Arch este și el programabil, ceea ce este util pentru propriile tale mapări. `archctl menu` îl deschide la rădăcină, și poți sări direct la orice punct din arbore numindu-l: `archctl menu summon style.theme` merge direct la selectorul de teme, `archctl menu toggle system` deschide meniul de sistem și îl închide din nou dacă este deja afișat, iar `archctl menu close` îl pune deoparte.
