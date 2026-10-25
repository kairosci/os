# Arch CLI

Arch styrs vanligtvis via snabbtangenterna och Arch-menyn (`Super + Space`). Men du kan också styra det via `arch` CLI. Detta är särskilt hjälpsamt när du låter en AI-agent arbeta med dig på anpassning eller konfiguration.

CLI:t har åtkomst till alla interna verktyg som används både via menyn och annars. Du kan se allt som är tillgängligt genom att köra `arch` i terminalen.

Det ser ut ungefär så här:

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

Och du kan dyka djupare i varje grupp:

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

Varje kommando tar också `--help`, oavsett om du frågar en hel grupp (`archctl capture --help`) eller ett enskilt kommando (`archctl capture screenshot --help`).

### Öppna menyn från terminalen

Arch-menyn är också skriptbar, vilket är praktiskt för dina egna tangentbindningar. `archctl menu` öppnar den vid roten, och du kan hoppa direkt till valfri punkt i trädet genom att namnge den: `archctl menu summon style.theme` går rakt till temaväljaren, `archctl menu toggle system` öppnar systemmenyn och stänger den igen om den redan är uppe, och `archctl menu close` lägger undan den.
