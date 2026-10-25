# Arch CLI

โดยปกติ Arch ควบคุมผ่านปุ่มลัดและเมนู Arch (`Super + Space`) แต่คุณยังควบคุมมันผ่าน CLI `arch` ได้เช่นกัน สิ่งนี้ช่วยได้เป็นพิเศษเมื่อคุณให้เอเจนต์ AI ทำงานร่วมกับคุณในการปรับแต่งหรือการกำหนดค่า

CLI เข้าถึงเครื่องมือภายในทั้งหมดที่ใช้ทั้งผ่านเมนูและวิธีอื่น ๆ ได้ คุณสามารถดูทุกสิ่งที่มีได้โดยการรัน `arch` ในเทอร์มินัล

มันมีหน้าตาอะไรแบบนี้:

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

และคุณลงลึกในทุกกลุ่มได้:

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

ทุกคำสั่งรับ `--help` ด้วย ไม่ว่าคุณจะถามทั้งกลุ่ม (`archctl capture --help`) หรือคำสั่งเดียว (`archctl capture screenshot --help`)

### การเปิดเมนูจากเทอร์มินัล

เมนู Arch ยังเขียนสคริปต์ได้เช่นกัน ซึ่งมีประโยชน์สำหรับการผูกปุ่มของคุณเอง `archctl menu` เปิดมันที่ราก และคุณกระโดดตรงไปยังจุดใด ๆ ในโครงสร้างโดยการตั้งชื่อมัน: `archctl menu summon style.theme` ตรงไปยังตัวเลือกธีม `archctl menu toggle system` เปิดเมนูระบบและปิดอีกครั้งหากมันเปิดอยู่แล้ว และ `archctl menu close` เก็บมันไว้
