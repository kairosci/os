# Arch CLI

Arch di solito si controlla tramite le scorciatoie e il menu Arch (`Super + Space`). Ma puoi anche controllarlo tramite la CLI `arch`. Questo è particolarmente utile quando hai un agente AI che lavora con te su personalizzazione o configurazione.

La CLI ha accesso a tutti gli strumenti interni usati sia tramite il menu che altrimenti. Puoi vedere tutto ciò che è disponibile eseguendo `arch` nel terminale.

Ha un aspetto simile a questo:

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

E puoi approfondire ogni gruppo:

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

Ogni comando accetta anche `--help`, che tu chieda un intero gruppo (`archctl capture --help`) o un singolo comando (`archctl capture screenshot --help`).

### Aprire il menu da terminale

Anche il menu Arch è scriptabile, il che è comodo per le tue combinazioni. `archctl menu` lo apre alla radice, e puoi saltare dritto a qualsiasi punto dell'albero nominandolo: `archctl menu summon style.theme` va dritto al selettore del tema, `archctl menu toggle system` apre il menu di sistema e lo chiude di nuovo se è già aperto, e `archctl menu close` lo mette via.
