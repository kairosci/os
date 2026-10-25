# Arch CLI

Arch odatda hotkeylar va Arch menyusi (`Super + Space`) orqali boshqariladi. Lekin uni `arch` CLI orqali ham boshqarishingiz mumkin. Bu, ayniqsa, AI agent siz bilan moslashuv yoki konfiguratsiya ustida ishlayotganda foydali.

CLI menyu orqali ham, boshqacha ham ishlatiladigan barcha ichki vositalarga kira oladi. Mavjud boʻlgan hamma narsani terminalda `arch` ni ishga tushirish orqali koʻrishingiz mumkin.

U taxminan mana bunday koʻrinadi:

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

Va har bir guruhga chuqurroq kirishingiz mumkin:

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

Har bir buyruq `--help` ni ham oladi, siz butun guruhdan (`archctl capture --help`) yoki bitta buyruqdan (`archctl capture screenshot --help`) soʻrasangiz ham.

### Menyuni terminaldan ochish

Arch menyusi ham skriptlashtirilishi mumkin, bu oʻz tugmalar bogʻlanishlaringiz uchun qulay. `archctl menu` uni ildizda ochadi va siz nom berish orqali daraxtning istalgan nuqtasiga toʻgʻridan-toʻgʻri sakrashingiz mumkin: `archctl menu summon style.theme` toʻgʻridan-toʻgʻri mavzu tanlovchiga boradi, `archctl menu toggle system` tizim menyusini ochadi va agar u allaqachon ochiq boʻlsa yana yopadi va `archctl menu close` uni yigʻishtiradi.
