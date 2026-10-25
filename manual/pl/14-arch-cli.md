# CLI Arch

Arch zwykle steruje się przez skróty oraz menu Arch (`Super + Space`). Ale możesz też sterować nim przez CLI `arch`. Jest to szczególnie pomocne, gdy pracujesz z agentem AI nad dostosowywaniem lub konfiguracją.

CLI ma dostęp do wszystkich wewnętrznych narzędzi używanych zarówno z menu, jak i w inny sposób. Wszystko, co jest dostępne, zobaczysz, uruchamiając `arch` w terminalu.

Wygląda to mniej więcej tak:

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

A do każdej grupy możesz wejść głębiej:

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

Każde polecenie przyjmuje też `--help`, niezależnie od tego, czy zapytasz całą grupę (`archctl capture --help`), czy pojedyncze polecenie (`archctl capture screenshot --help`).

### Otwieranie menu z terminala

Menu Arch jest też skryptowalne, co jest przydatne do własnych przypisań klawiszy. `archctl menu` otwiera je u nasady, a możesz wskoczyć wprost do dowolnego punktu drzewa, nazywając go: `archctl menu summon style.theme` idzie od razu do wyboru motywu, `archctl menu toggle system` otwiera menu systemowe i zamyka je ponownie, jeśli jest już otwarte, a `archctl menu close` je chowa.
