# CLI Arch

Arch se contrôle habituellement via les raccourcis clavier et le menu Arch (`Super + Space`). Mais vous pouvez aussi le contrôler via la CLI `arch`. C'est particulièrement utile lorsque vous faites travailler un agent IA avec vous sur la personnalisation ou la configuration.

La CLI a accès à tous les outils internes utilisés à la fois via le menu et autrement. Vous pouvez voir tout ce qui est disponible en exécutant `arch` dans le terminal.

Cela ressemble à ceci :

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

Et vous pouvez approfondir chaque groupe :

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

Chaque commande accepte aussi `--help`, que vous interrogiez un groupe entier (`archctl capture --help`) ou une seule commande (`archctl capture screenshot --help`).

### Ouvrir le menu depuis le terminal

Le menu Arch est également scriptable, ce qui est pratique pour vos propres raccourcis. `archctl menu` l'ouvre à la racine, et vous pouvez sauter directement à n'importe quel point de l'arborescence en le nommant : `archctl menu summon style.theme` va directement au sélecteur de thème, `archctl menu toggle system` ouvre le menu système et le referme s'il est déjà ouvert, et `archctl menu close` le range.
