# CLI do Arch

O Arch geralmente é controlado pelos atalhos e pelo menu do Arch (`Super + Space`). Mas você também pode controlá-lo pela CLI `arch`. Isso é particularmente útil quando você tem um agente de IA trabalhando com você em personalização ou configuração.

A CLI tem acesso a todas as ferramentas internas usadas tanto pelo menu quanto de outras formas. Você pode ver tudo o que está disponível executando `arch` no terminal.

Ela se parece com algo assim:

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

E você pode mergulhar mais fundo em cada grupo:

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

Todo comando também aceita `--help`, quer você pergunte a um grupo inteiro (`archctl capture --help`) ou a um único comando (`archctl capture screenshot --help`).

### Abrindo o menu pelo terminal

O menu do Arch também é programável por script, o que é útil para seus próprios atalhos. `archctl menu` o abre na raiz, e você pode pular direto para qualquer ponto da árvore nomeando-o: `archctl menu summon style.theme` vai direto ao seletor de temas, `archctl menu toggle system` abre o menu do sistema e o fecha de novo se já estiver aberto, e `archctl menu close` o guarda.
