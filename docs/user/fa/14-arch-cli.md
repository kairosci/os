# Arch CLI

Arch معمولاً از طریق کلیدهای میانبر و منوی Arch (`Super + Space`) کنترل می‌شود. اما همچنین می‌توانید آن را از طریق CLI ـی `arch` کنترل کنید. این به‌ویژه وقتی یک عامل هوش مصنوعی در سفارشی‌سازی یا پیکربندی با شما کار می‌کند مفید است.

CLI به همهٔ ابزارهای درونی که هم از طریق منو و هم در غیر این صورت استفاده می‌شوند دسترسی دارد. می‌توانید با اجرای `arch` در ترمینال همهٔ آنچه در دسترس است را ببینید.

تقریباً این‌گونه به نظر می‌رسد:

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

و می‌توانید در هر گروه عمیق‌تر شوید:

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

هر فرمان همچنین `--help` را می‌پذیرد، چه یک گروه کامل را بپرسید (`archctl capture --help`) یا یک فرمان واحد (`archctl capture screenshot --help`).

### باز کردن منو از ترمینال

منوی Arch همچنین قابل اسکریپت‌نویسی است، که برای نگاشت‌های کلیدی خودتان مفید است. `archctl menu` آن را در ریشه باز می‌کند و می‌توانید با نام‌بردن مستقیماً به هر نقطه‌ای در درخت بروید: `archctl menu summon style.theme` مستقیماً به انتخاب‌گر تم می‌رود، `archctl menu toggle system` منوی سیستم را باز می‌کند و اگر از قبل باز باشد دوباره آن را می‌بندد و `archctl menu close` آن را کنار می‌گذارد.
