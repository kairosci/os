# Arch CLI

Arch genellikle kısayollar ve Arch menüsü (`Super + Space`) yoluyla denetlenir. Ancak onu `arch` CLI yoluyla da denetleyebilirsiniz. Bu, özellikle bir AI ajanını özelleştirme veya yapılandırma konusunda sizinle çalıştırırken yararlıdır.

CLI, hem menü yoluyla hem de başka şekilde kullanılan tüm dahili araçlara erişime sahiptir. Terminalde `arch` çalıştırarak kullanılabilir her şeyi görebilirsiniz.

Şöyle bir şeye benzer:

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

Ve her gruba daha derine inebilirsiniz:

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

Her komut `--help` de alır; ister tüm bir grubu sorun (`archctl capture --help`) ister tek bir komutu sorun (`archctl capture screenshot --help`).

### Menüyü terminalden açmak

Arch menüsü de betiklenebilir; bu kendi tuş bağlamalarınız için kullanışlıdır. `archctl menu` onu kökte açar ve adını vererek ağaçtaki herhangi bir noktaya doğrudan atlayabilirsiniz: `archctl menu summon style.theme` doğrudan tema seçiciye gider, `archctl menu toggle system` sistem menüsünü açar ve zaten açıksa tekrar kapatır ve `archctl menu close` onu kaldırır.
