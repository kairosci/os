# Arch CLI

Arch biasanya dikawal melalui kekunci panas dan menu Arch (`Super + Space`). Tetapi anda juga boleh mengawalnya melalui CLI `arch`. Ini amat membantu apabila anda meminta ejen AI bekerja dengan anda mengenai penyesuaian atau konfigurasi.

CLI mempunyai akses kepada semua perkakasan dalaman yang digunakan melalui menu dan sebaliknya. Anda boleh melihat semua yang tersedia dengan menjalankan `arch` dalam terminal.

Ia kelihatan seperti ini:

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

Dan anda boleh menyelami lebih mendalam pada setiap kumpulan:

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

Setiap arahan juga mengambil `--help`, sama ada anda bertanya keseluruhan kumpulan (`archctl capture --help`) atau satu arahan (`archctl capture screenshot --help`).

### Membuka menu dari terminal

Menu Arch juga boleh diskrip, yang berguna untuk ikatan kekunci anda sendiri. `archctl menu` membukanya pada akar, dan anda boleh melompat terus ke mana-mana titik dalam pokok dengan menamainya: `archctl menu summon style.theme` pergi terus ke pemilih Tema, `archctl menu toggle system` membuka menu Sistem dan menutupnya semula jika ia sudah dipaparkan, dan `archctl menu close` menyimpannya.
