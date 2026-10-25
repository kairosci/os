# Arch CLI

Arch paprastai valdoma per sparčiuosius klavišus ir Arch meniu (`Super + Space`). Bet taip pat galite ją valdyti per `arch` CLI. Tai ypač naudinga, kai AI agentas dirba su jumis prie pritaikymo ar konfigūracijos.

CLI turi prieigą prie visų vidinių įrankių, kurie naudojami tiek per meniu, tiek kitaip. Viską, kas prieinama, galite pamatyti terminale paleisdami `arch`.

Tai atrodo maždaug taip:

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

Ir galite gilintis į kiekvieną grupę:

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

Kiekviena komanda taip pat priima `--help`, nesvarbu, ar klausiate visos grupės (`archctl capture --help`), ar vienos komandos (`archctl capture screenshot --help`).

### Meniu atidarymas iš terminalo

Arch meniu taip pat galima užprogramuoti scenarijais, o tai patogu jūsų pačių klavišų susiejimams. `archctl menu` atidaro jį šaknyje, ir galite šokti tiesiai į bet kurį medžio tašką jį įvardydami: `archctl menu summon style.theme` eina tiesiai į temų parinkiklį, `archctl menu toggle system` atidaro sistemos meniu ir vėl jį uždaro, jei jis jau atidarytas, o `archctl menu close` jį padeda.
