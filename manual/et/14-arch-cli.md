# Arch CLI

Archt juhitakse tavaliselt kiirklahvide ja Arch menüü kaudu (`Super + Space`). Kuid saad seda juhtida ka `arch` CLI kaudu. See on eriti abiks, kui sul on AI agent, kes töötab sinuga kohandamise või seadistamise kallal.

CLI-l on juurdepääs kogu sisemisele tööriistakastile, mida kasutatakse nii menüü kui ka muul viisil. Saad näha kõike saadaolevat, käivitades terminalis `arch`.

See näeb välja umbes nii:

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

Ja saad igasse rühma sügavamale sukelduda:

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

Iga käsk võtab ka `--help`, olenemata sellest, kas küsid tervet rühma (`archctl capture --help`) või ühte käsku (`archctl capture screenshot --help`).

### Menüü avamine terminalist

Arch menüü on samuti skriptitav, mis on sinu enda klahviseoste jaoks käepärane. `archctl menu` avab selle juure juures ja saad hüpata otse puu mis tahes punkti, nimetades selle: `archctl menu summon style.theme` läheb otse teemavalija juurde, `archctl menu toggle system` avab süsteemi menüü ja sulgeb selle uuesti, kui see juba üleval on, ja `archctl menu close` paneb selle ära.
