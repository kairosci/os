# Arch CLI

Arch wird normalerweise über die Tastenkürzel und das Arch-Menü (`Super + Space`) gesteuert. Aber du kannst es auch über die `arch`-CLI steuern. Das ist besonders hilfreich, wenn ein KI-Agent mit dir an Anpassung oder Konfiguration arbeitet.

Die CLI hat Zugriff auf alle internen Werkzeuge, die sowohl über das Menü als auch anderweitig verwendet werden. Du kannst alles sehen, was verfügbar ist, indem du `arch` im Terminal ausführst.

Es sieht ungefähr so aus:

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

Und du kannst bei jeder Gruppe tiefer eintauchen:

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

Jeder Befehl akzeptiert auch `--help`, egal ob du eine ganze Gruppe fragst (`archctl capture --help`) oder einen einzelnen Befehl (`archctl capture screenshot --help`).

### Das Menü vom Terminal aus öffnen

Das Arch-Menü ist ebenfalls skriptbar, was für deine eigenen Tastenzuordnungen praktisch ist. `archctl menu` öffnet es an der Wurzel, und du kannst direkt zu jedem Punkt im Baum springen, indem du ihn benennst: `archctl menu summon style.theme` geht direkt zur Design-Auswahl, `archctl menu toggle system` öffnet das Systemmenü und schließt es wieder, wenn es bereits offen ist, und `archctl menu close` räumt es weg.
