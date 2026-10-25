# Arch CLI

Archä ohjataan yleensä pikanäppäinten ja Arch-valikon kautta (`Super + Space`). Mutta voit ohjata sitä myös `arch` CLI:n kautta. Tämä on erityisen hyödyllistä, kun sinulla on tekoälyagentti työstämässä kanssasi mukautuksia tai määrityksiä.

CLI:llä on pääsy kaikkiin sisäisiin työkaluihin, joita käytetään sekä valikon kautta että muuten. Näet kaiken saatavilla olevan ajamalla pääätteessä komennon `arch`.

Se näyttää suunnilleen tältä:

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

Ja voit sukeltaa syvemmälle jokaiseen ryhmään:

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

Jokainen komento hyväksyy myös valitsimen `--help`, kysyitpä kokonaisen ryhmän (`archctl capture --help`) tai yhden komennon (`archctl capture screenshot --help`) ohjetta.

### Valikon avaaminen pääätteestä

Myös Arch-valikko on skriptattavissa, mikä on kätevää omia pikanäppäimiäsi varten. `archctl menu` avaa sen juuresta, ja voit hypätä suoraan mihin tahansa puun kohtaan nimeämällä sen: `archctl menu summon style.theme` menee suoraan teeman valitsimeen, `archctl menu toggle system` avaa järjestelmävalikon ja sulkee sen uudelleen, jos se on jo avoinna, ja `archctl menu close` sulkee sen kokonaan.
