# Arch CLI

Az Archt általában a billentyűparancsokkal és az Arch menüvel (`Super + Space`) vezérlik. De az `arch` CLI-n keresztül is vezérelheted. Ez különösen hasznos, amikor egy AI-agenttel dolgozol együtt testreszabási vagy konfigurációs feladatokon.

A CLI hozzáfér az összes belső eszközhöz, amelyet mind a menün keresztül, mind máshol használnak. Mindent láthatsz, ami rendelkezésre áll, ha terminálban futtatod az `arch` parancsot.

Valahogy így néz ki:

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

És minden csoportban mélyebbre merülhetsz:

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

Minden parancs elfogadja a `--help` kapcsolót is, akár egy egész csoporttól kérdezed (`archctl capture --help`), akár egyetlen parancstól (`archctl capture screenshot --help`).

### A menü megnyitása a terminálból

Az Arch menü szkriptelhető is, ami jól jön a saját billentyűhozzárendeléseidhez. Az `archctl menu` a gyökérnél nyitja meg, és a fában egyenesen bármely pontra ugorhatsz, ha megnevezed: az `archctl menu summon style.theme` egyenesen a témaválasztóhoz megy, az `archctl menu toggle system` megnyitja a rendszermenüt, és ismét bezárja, ha már nyitva van, az `archctl menu close` pedig elteszi.
