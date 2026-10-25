# CLI Arch

Arch se običajno nadzira prek bližnjic in menija Arch (`Super + Space`). Lahko pa ga nadzirate tudi prek CLI `arch`. To je še posebej koristno, kadar vam agent AI pomaga pri prilagajanju ali konfiguraciji.

CLI ima dostop do vsega notranjega orodjarjenja, ki se uporablja tako prek menija kot sicer. Vse, kar je na voljo, si lahko ogledate tako, da v terminalu zaženete `arch`.

Videti je nekako takole:

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

V vsako skupino se lahko poglobite:

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

Vsak ukaz sprejme tudi `--help`, ne glede na to, ali prosite za celotno skupino (`archctl capture --help`) ali en sam ukaz (`archctl capture screenshot --help`).

### Odpiranje menija iz terminala

Meni Arch je mogoče skriptati tudi, kar je priročno za lastne vezave tipk. `archctl menu` ga odpre v korenu, skočite pa lahko naravnost na kateri koli točki drevesa, če ga poimenujete: `archctl menu summon style.theme` gre naravnost do izbirnika teme, `archctl menu toggle system` odpre sistemski meni in ga znova zapre, če je že odprt, `archctl menu close` pa ga spravi stran.
