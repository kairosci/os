# Arch CLI

Arch عام طور پر ہاٹ کیز اور Arch مینیُو (`Super + Space`) کے ذریعے کنٹرول کیا جاتا ہے۔ لیکن آپ اسے `arch` CLI کے ذریعے بھی کنٹرول کر سکتے ہیں۔ یہ خاص طور پر اس وقت مددگار ہوتا ہے جب آپ AI ایجنٹ کو کسٹمائزیشن یا کنفیگریشن پر اپنے ساتھ کام کرا رہے ہوں۔

CLI کو ان تمام داخلی ٹولز تک رسائی حاصل ہے جو مینیُو کے ذریعے بھی استعمال ہوتے ہیں اور دوسری جگہ بھی۔ آپ ٹرمینل میں `arch` چلا کر دستیاب سب کچھ دیکھ سکتے ہیں۔

یہ کچھ اس طرح لگتا ہے:

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

اور آپ ہر گروپ پر مزید گہرائی میں جا سکتے ہیں:

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

ہر کمانڈ `--help` بھی لیتی ہے، چاہے آپ پورا گروپ پوچھیں (`archctl capture --help`) یا کوئی ایک کمانڈ (`archctl capture screenshot --help`)۔

### ٹرمینل سے مینیُو کھولنا

Arch مینیُو بھی اسکرپٹ کے قابل ہے، جو آپ کی اپنی کی بائنڈنگز کے لیے سودمند ہے۔ `archctl menu` اسے جڑ پر کھولتا ہے، اور آپ اس کا نام دے کر درخت میں کسی بھی مقام پر براہ راست جا سکتے ہیں: `archctl menu summon style.theme` سیدھا تھیم پِکر پر جاتا ہے، `archctl menu toggle system` سسٹم مینیُو کھولتا ہے اور اگر یہ پہلے سے اوپر ہے تو اسے دوبارہ بند کر دیتا ہے، اور `archctl menu close` اسے ہٹا دیتا ہے۔
