# Arch CLI

يُتحكّم في Arch عادة عبر اختصارات المفاتيح وقائمة Arch (`Super + Space`). لكن يمكنك أيضًا التحكّم فيه عبر `arch` CLI. هذا مفيد بشكل خاص عندما يكون لديك وكيل AI يعمل معك على تخصيص أو تكوين.

لـ CLI وصول إلى كل الأدوات الداخلية المستخدمة عبر القائمة وبخلاف ذلك. يمكنك رؤية كل شيء متاح بتشغيل `arch` في الطرفية.

يبدو شيئًا كهذا:

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

ويمكنك الغوص أعمق في كل مجموعة:

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

كل أمر يأخذ `--help` أيضًا، سواء سألت مجموعة كاملة (`archctl capture --help`) أو أمرًا واحدًا (`archctl capture screenshot --help`).

### فتح القائمة من الطرفية

قائمة Arch قابلة للبرمجة النصية أيضًا، وهو ما هو مفيد لروابط مفاتيحك الخاصة. `archctl menu` يفتحها في الجذر، ويمكنك القفز مباشرة إلى أي نقطة في الشجرة بتسميتها: `archctl menu summon style.theme` يذهب مباشرة إلى منتقي السمات، و`archctl menu toggle system` يفتح قائمة النظام ويغلقها مرة أخرى إذا كانت مفتوحة بالفعل، و`archctl menu close` يضعها بعيدًا.
