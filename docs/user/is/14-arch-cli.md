# Arch CLI

Arch er venjulega stjórnað með flýtilyklunum og Arch-valmyndinni (`Super + Space`). En þú getur líka stjórnað því í gegnum `arch` CLI. Þetta er sérstaklega gagnlegt þegar þú lætur gervigreindar-agent vinna með þér að aðlögun eða stillingum.

CLI-ið hefur aðgang að öllum innri verkfærunum sem eru notuð bæði í gegnum valmyndina og annars staðar. Þú getur séð allt sem er í boði með því að keyra `arch` í terminalnum.

Það lítur svona út:

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

Og þú getur kafað dýpra í hvern hóp:

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

Sérhver skipun tekur líka við `--help`, hvort sem þú biður allan hópinn (`archctl capture --help`) eða eina skipun (`archctl capture screenshot --help`).

### Að opna valmyndina úr terminalnum

Arch-valmyndin er einnig forskriftahæf, sem er þægilegt fyrir þínar eigin lyklatengingar. `archctl menu` opnar hana við rótina, og þú getur hoppað beint á hvaða punkt sem er í trénu með því að nefna hann: `archctl menu summon style.theme` fer beint í þemavalinn, `archctl menu toggle system` opnar kerfisvalmyndina og lokar henni aftur ef hún er þegar uppi, og `archctl menu close` setur hana í burtu.
