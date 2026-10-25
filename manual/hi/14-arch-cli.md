# Arch CLI

Arch को आमतौर पर हॉटकी और Arch मेनू (`Super + Space`) के ज़रिए नियंत्रित किया जाता है। लेकिन आप इसे `arch` CLI के ज़रिए भी नियंत्रित कर सकते हैं। यह विशेष रूप से तब मददगार होता है जब कोई AI एजेंट अनुकूलन या कॉन्फ़िगरेशन पर आपके साथ काम कर रहा हो।

CLI के पास सभी आंतरिक उपकरणों तक पहुँच है जिनका इस्तेमाल मेनू के ज़रिए भी किया जाता है और अन्यथा भी। आप टर्मिनल में `arch` चलाकर उपलब्ध सभी चीज़ों को देख सकते हैं।

यह कुछ इस तरह दिखता है:

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

और आप हर समूह में और गहराई से जा सकते हैं:

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

हर कमांड `--help` भी लेता है, चाहे आप पूरा समूह पूछें (`archctl capture --help`) या कोई एक कमांड (`archctl capture screenshot --help`)।

### टर्मिनल से मेनू खोलना

Arch मेनू भी स्क्रिप्ट करने योग्य है, जो आपकी अपनी कीबाइंडिंग के लिए उपयोगी है। `archctl menu` उसे जड़ पर खोलता है, और आप उसका नाम लेकर वृक्ष के किसी भी बिंदु पर सीधे जा सकते हैं: `archctl menu summon style.theme` सीधे थीम पिकर पर जाता है, `archctl menu toggle system` सिस्टम मेनू खोलता है और अगर वह पहले से खुला है तो उसे फिर से बंद कर देता है, और `archctl menu close` उसे हटा देता है।
