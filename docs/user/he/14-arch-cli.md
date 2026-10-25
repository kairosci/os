# CLI של Arch

Arch נשלטת בדרך כלל דרך קיצורי המקלדת ותפריט Arch (`Super + Space`). אבל אפשר גם לשלוט בה דרך ה-CLI של `arch`. זה שימושי במיוחד כאשר סוכן AI עובד איתכם על התאמה אישית או הגדרה.

ל-CLI יש גישה לכל הכלים הפנימיים שנמצאים בשימוש הן דרך התפריט והן בדרכים אחרות. אפשר לראות את כל מה שזמין על ידי הרצת `arch` בטרמינל.

זה נראה בערך כך:

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

ואפשר לצלול עמוק יותר בכל קבוצה:

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

כל פקודה מקבלת גם את `--help`, בין אם שואלים קבוצה שלמה (`archctl capture --help`) או פקודה בודדת (`archctl capture screenshot --help`).

### פתיחת התפריט מהטרמינל

תפריט Arch ניתן גם לתסריט, מה שנחמד לשיוכי המקשים שלכם. הפקודה `archctl menu` פותחת אותו בשורש, ואפשר לקפוץ ישירות לכל נקודה בעץ על ידי ציון שמה: `archctl menu summon style.theme` עובר ישר לבורר ערכות הנושא, `archctl menu toggle system` פותח את תפריט המערכת וסוגר אותו שוב אם הוא כבר פתוח, ו-`archctl menu close` מסלק אותו.
