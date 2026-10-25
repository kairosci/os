# CLI Arch

Arch biasanya dikontrol melalui hotkey dan menu Arch (`Super + Space`). Namun Anda juga dapat mengontrolnya melalui CLI `arch`. Ini sangat membantu ketika Anda memiliki agen AI yang bekerja dengan Anda dalam kustomisasi atau konfigurasi.

CLI memiliki akses ke semua perkakas internal yang digunakan baik melalui menu maupun sebaliknya. Anda dapat melihat semua yang tersedia dengan menjalankan `arch` di terminal.

Ia terlihat seperti ini:

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

Dan Anda dapat menyelami lebih dalam pada setiap grup:

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

Setiap perintah juga menerima `--help`, apakah Anda menanyakan seluruh grup (`archctl capture --help`) atau satu perintah (`archctl capture screenshot --help`).

### Membuka menu dari terminal

Menu Arch juga dapat diskrip, yang berguna untuk keybinding Anda sendiri. `archctl menu` membukanya di akar, dan Anda dapat langsung melompat ke titik mana pun dalam pohon dengan menamainya: `archctl menu summon style.theme` langsung menuju pemilih tema, `archctl menu toggle system` membuka menu sistem dan menutupnya lagi jika sudah terbuka, dan `archctl menu close` menutupnya.
