# Arch CLI

Arch සාමාන්‍යයෙන් පාලනය වන්නේ උණුසුම් යතුරු සහ Arch මෙනුව (`Super + Space`) හරහායි. නමුත් ඔබට එය `arch` CLI හරහා ද පාලනය කළ හැකිය. ඔබ අභිරුචිකරණය හෝ වින්‍යාසය පිළිබඳව AI නියෝජිතයෙකු ඔබ සමඟ වැඩ කරන විට මෙය විශේෂයෙන් ප්‍රයෝජනවත් වේ.

CLI එකට මෙනුව හරහා සහ වෙනත් ආකාරයකින් භාවිතා කරන සියලුම අභ්‍යන්තර මෙවලම් වෙත ප්‍රවේශය ඇත. ටර්මිනලයේ `arch` ධාවනය කිරීමෙන් ලබා ගත හැකි සියල්ල ඔබට දැකිය හැකිය.

එය මේ වගේ දෙයක් පෙනේ:

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

ඔබට සෑම කණ්ඩායමක් පිළිබඳවම ගැඹුරට කිමිදිය හැකිය:

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

ඔබ මුළු කණ්ඩායමක් (`archctl capture --help`) හෝ තනි විධානයක් (`archctl capture screenshot --help`) ඇසුවත් සෑම විධානයක්ම `--help` ද ගනී.

### ටර්මිනලයෙන් මෙනුව විවෘත කිරීම

Arch මෙනුව ස්ක්‍රිප්ට් කළ හැකි අතර, එය ඔබේම යතුරු බන්ධන සඳහා ප්‍රයෝජනවත් වේ. `archctl menu` එය මූලයේ විවෘත කරන අතර, ඔබට එය නම් කිරීමෙන් ගසේ ඕනෑම ස්ථානයකට කෙලින්ම පැනිය හැකිය: `archctl menu summon style.theme` කෙලින්ම තේමා තේරීමට යයි, `archctl menu toggle system` පද්ධති මෙනුව විවෘත කරන අතර එය දැනටමත් ඉහළට පැමිණ ඇත්නම් එය නැවත වසයි, සහ `archctl menu close` එය ඉවත් කරයි.
