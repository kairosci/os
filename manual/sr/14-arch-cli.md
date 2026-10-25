# Arch CLI

Arch се обично контролише преко пречица и Arch менија (`Super + Space`). Али можете га контролисати и преко `arch` CLI-ја. Ово је посебно корисно кад AI агент ради с вама на прилагођавању или конфигурацији.

CLI има приступ свим интерним алатима који се користе и преко менија и иначе. Све што је доступно можете видети покретањем `arch` у терминалу.

Изгледа отприлике овако:

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

И можете заронити дубље у сваку групу:

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

Свака команда такође прихвата `--help`, било да питате целу групу (`archctl capture --help`) или једну команду (`archctl capture screenshot --help`).

### Отварање менија из терминала

Arch мени је такође скриптабилан, што је згодно за ваше сопствене пречице тастатуре. `archctl menu` га отвара у корену, а можете скочити право на било коју тачку у стаблу именовањем: `archctl menu summon style.theme` иде право на бирач тема, `archctl menu toggle system` отвара системски мени и поново га затвара ако је већ отворен, а `archctl menu close` га склања.
