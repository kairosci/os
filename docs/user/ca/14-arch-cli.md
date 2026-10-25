# CLI d'Arch

Arch normalment es controla mitjançant les dreceres i el menú d'Arch (`Super + Space`). Però també el podeu controlar mitjançant la CLI `arch`. Això és especialment útil quan teniu un agent d'IA treballant amb vosaltres en la personalització o la configuració.

La CLI té accés a totes les eines internes que es fan servir tant des del menú com d'altres maneres. Podeu veure tot el que hi ha disponible executant `arch` al terminal.

És una cosa així:

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

I podeu aprofundir en cada grup:

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

Cada ordre també accepta `--help`, tant si demaneu a tot un grup (`archctl capture --help`) com a una sola ordre (`archctl capture screenshot --help`).

### Obrir el menú des del terminal

El menú d'Arch també es pot programar, cosa útil per a les vostres pròpies dreceres. `archctl menu` l'obre a l'arrel, i podeu saltar directament a qualsevol punt de l'arbre anomenant-lo: `archctl menu summon style.theme` va directament al selector de temes, `archctl menu toggle system` obre el menú del sistema i el torna a tancar si ja és obert, i `archctl menu close` el desa.
