# Arch CLI

Arch thường được điều khiển qua các phím tắt và menu Arch (`Super + Space`). Nhưng bạn cũng có thể điều khiển nó qua CLI `arch`. Điều này đặc biệt hữu ích khi bạn có một AI agent làm việc cùng bạn về tùy chỉnh hoặc cấu hình.

CLI có quyền truy cập vào mọi công cụ nội bộ được dùng cả qua menu và bằng cách khác. Bạn có thể xem mọi thứ khả dụng bằng cách chạy `arch` trong terminal.

Nó trông giống như thế này:

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

Và bạn có thể đi sâu hơn vào mọi nhóm:

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

Mọi lệnh cũng nhận `--help`, dù bạn hỏi một nhóm toàn bộ (`archctl capture --help`) hay một lệnh duy nhất (`archctl capture screenshot --help`).

### Mở menu từ terminal

Menu Arch cũng có thể viết tập lệnh được, điều này tiện dụng cho các phím gán của riêng bạn. `archctl menu` mở nó ở gốc, và bạn có thể nhảy thẳng tới bất kỳ điểm nào trong cây bằng cách đặt tên cho nó: `archctl menu summon style.theme` đi thẳng tới bộ chọn chủ đề, `archctl menu toggle system` mở menu hệ thống và đóng nó lại nếu nó đã hiển thị, và `archctl menu close` cất nó đi.
