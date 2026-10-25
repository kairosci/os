# Arch CLI

Arch는 보통 단축키와 Arch 메뉴(`Super + Space`)를 통해 제어합니다. 하지만 `arch` CLI를 통해서도 제어할 수 있습니다. 특히 AI 에이전트와 함께 사용자 지정이나 구성을 작업할 때 유용합니다.

CLI는 메뉴 등을 통해 사용되는 모든 내부 도구에 접근할 수 있습니다. 터미널에서 `arch`를 실행하면 사용 가능한 모든 것을 볼 수 있습니다.

모습은 다음과 비슷합니다:

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

그리고 모든 그룹에 대해 더 깊이 파고들 수 있습니다:

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

모든 명령은 `--help`도 지원합니다. 전체 그룹에 대해 물어보든(`archctl capture --help`) 단일 명령에 대해 물어보든(`archctl capture screenshot --help`) 마찬가지입니다.

### 터미널에서 메뉴 열기

Arch 메뉴도 스크립트화할 수 있어, 직접 키바인딩을 만들 때 유용합니다. `archctl menu`는 루트에서 메뉴를 열고, 이름을 지정하면 트리의 어느 지점으로든 바로 이동할 수 있습니다. `archctl menu summon style.theme`은 테마 선택기로 바로 가고, `archctl menu toggle system`은 시스템 메뉴를 열었다가 이미 열려 있으면 다시 닫으며, `archctl menu close`는 메뉴를 치웁니다.
