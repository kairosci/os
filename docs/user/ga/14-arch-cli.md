# Arch CLI

De ghnáth rialaítear Arch trí na heochracha gasta agus roghchlár Arch (`Super + Space`). Ach is féidir leat é a rialú freisin trí CLI `arch`. Tá sé seo an-chabhrach go háirithe nuair a bhíonn gníomhaire AI ag obair leat ar shaincheapadh nó ar chumraíocht.

Tá rochtain ag an CLI ar an uirlisiú inmheánach ar fad a úsáidtear tríd an roghchlár agus ar shlí eile araon. Is féidir leat gach rud atá ar fáil a fheiceáil trí `arch` a rith sa teirminéal.

Tá cuma air rud éigin mar seo:

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

Agus is féidir leat dul níos doimhne ar gach grúpa:

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

Glacann gach ordú le `--help` freisin, cibé acu a fhiafraíonn tú de ghrúpa iomlán (`archctl capture --help`) nó d'ordú aonair (`archctl capture screenshot --help`).

### An roghchlár a oscailt ón teirminéal

Is féidir roghchlár Arch a scriptiú freisin, atá áisiúil do do cheangail eochracha féin. Osclaíonn `archctl menu` ag an bhfréamh é, agus is féidir leat léim go díreach chuig aon phointe sa chrann trí é a ainmniú: téann `archctl menu summon style.theme` go díreach chuig an roghnóir téama, osclaíonn `archctl menu toggle system` roghchlár an chórais agus dúnann sé arís é má tá sé suas cheana, agus cuireann `archctl menu close` ar shiúl é.
