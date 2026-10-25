# Arch CLI

Arch parasti kontrolē, izmantojot karstās taustiņu kombinācijas un Arch izvēlni (`Super + Space`). Bet tu vari to kontrolēt arī, izmantojot `arch` CLI. Tas ir īpaši noderīgi, kad tev ir AI aģents, kas strādā ar tevi pie pielāgošanas vai konfigurēšanas.

CLI ir piekļuve visiem iekšējiem rīkiem, ko izmanto gan caur izvēlni, gan citādi. Tu vari redzēt visu, kas ir pieejams, palaižot `arch` terminālī.

Tas izskatās apmēram šādi:

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

Un tu vari iedziļināties katrā grupā:

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

Katru komandu var izsaukt arī ar `--help`, neatkarīgi no tā, vai tu jautā visai grupai (`archctl capture --help`) vai vienai komandai (`archctl capture screenshot --help`).

### Izvēlnes atvēršana no termināla

Arch izvēlne ir arī skriptējama, kas ir ērti tavām taustiņu piesaistēm. `archctl menu` atver to saknē, un tu vari lekt tieši uz jebkuru punktu kokā, nosaucot to: `archctl menu summon style.theme` dodas tieši uz tēmu atlasītāju, `archctl menu toggle system` atver sistēmas izvēlni un atkal to aizver, ja tā jau ir augšā, un `archctl menu close` to novāc.
