# CLI de Arch

Arch normalmente se controla con los atajos de teclado y el menú de Arch (`Super + Space`). Pero también puedes controlarlo con la CLI `arch`. Esto es especialmente útil cuando tienes a un agente de IA trabajando contigo en personalización o configuración.

La CLI tiene acceso a todas las herramientas internas que se usan tanto desde el menú como por otros medios. Puedes ver todo lo disponible ejecutando `arch` en la terminal.

Se ve más o menos así:

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

Y puedes profundizar en cada grupo:

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

Cada comando también acepta `--help`, ya sea que le preguntes a un grupo completo (`archctl capture --help`) o a un solo comando (`archctl capture screenshot --help`).

### Abrir el menú desde la terminal

El menú de Arch también se puede controlar con scripts, lo cual es práctico para tus propios atajos. `archctl menu` lo abre en la raíz, y puedes saltar directo a cualquier punto del árbol nombrándolo: `archctl menu summon style.theme` va directo al selector de temas, `archctl menu toggle system` abre el menú del sistema y lo cierra si ya está abierto, y `archctl menu close` lo esconde.
