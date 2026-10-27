# Arch CLI

Arch is usually controlled through the hotkeys and the Arch menu (`Super + Space`). But you can also control it through the `arch` CLI. This is particularly helpful for customization and configuration.

The CLI has access to all the internal tooling that is used both via the menu and otherwise. You can see everything that's available by running `arch` in the terminal.

It looks something like this:

```
~ ❯ arch
Arch command center

Usage:
  arch <command> [args...]
  archctl commands [--all] [--json] [--check]
  arch <group> --help
  arch <group> <command> --help

Common commands:
  archctl update              Update Arch and system packages
  archctl theme list          List available themes
  archctl theme set <name>    Apply a theme
  archctl font list           List available fonts
  archctl screenshot          Take a screenshot
  archctl debug               Print debugging information

Groups:
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

And you can dive deeper on every group:

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

Every command takes `--help` too, whether you ask a whole group (`archctl capture --help`) or a single command (`archctl capture screenshot --help`).

### Opening the menu from the terminal

The Arch menu is scriptable as well, which is handy for your own keybindings. `archctl menu` opens it at the root, and you can jump straight to any point in the tree by naming it: `archctl menu summon appearance.theme` goes right to the theme picker, `archctl menu toggle system` opens the system menu and closes it again if it's already up, and `archctl menu close` puts it away.
