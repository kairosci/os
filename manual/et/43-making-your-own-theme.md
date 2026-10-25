# Oma teema tegemine

Sa saad lisada oma teemasid kausta `~/.config/arch/themes`. Kopeeri lihtsalt üks olemasolevatest aluseks (vaata kausta `/usr/share/arch/themes`) ja kohanda siis oma rõõmuks. Kuni sinu teema on seal kaustas, kaasatakse see teemavaliku menüüsse.

Põhifail, mida pead kohandama, on `colors.toml`. See määratleb värvikomplekti, mida seejärel kasutatakse seadistuste genereerimiseks terminalile (Foot/Alacritty/Ghostty/Kitty), btopile, Chromiumile, Hyprlandile, Neovimile, Helixile, VSCode'ile, Obsidianile ja kogu Arch kestale (menüüriba, menüü, teavitused, OSD ja lukuekraan).

Sa saad uue teema loomiseks kasutada ka kaasasolevat Aether rakendust, kasutades armsat graafilist liidest, et värvidega mängida ja taustu otsida. Käivita see lihtsalt rakenduste ruudustikult klahvikombinatsiooniga `Super + Alt + Space`.

### Mida paigaldatud teema võib sisaldada

Teema, mille kirjutad ise kausta `~/.config/arch/themes`, võib sisaldada mida iganes — see on sinu masin ja sinu fail ning Arch rakendab seda kõike.

Teema, mille paigaldad kellegi teise repositooriumist käsuga `archctl theme install`, säilitab kõik, mis on värv, ja kaotab need vähesed failid, mis sinu masinal koodi käivitaksid: iga `.lua` faili, terminali seadistused (`alacritty.toml`, `foot.ini`, `ghostty.conf`, `kitty.conf`) ja faili `vscode.json`. Teema `hyprland.lua` on Lua, mida sinu komposiitor sisselogimisel käivitab, terminali seadistus nimetab programmi, mida sinu terminal käivitab, ja `vscode.json` nimetab paigaldatava VSCode laienduse. Kellegi teema paigaldamine peaks muutma seda, milline sinu töölaud välja näeb, mitte kunagi seda, mida see käivitab.

Kõik muu töötab edasi täpselt nii, nagu teema autor kirjutas — `btop.theme`, `chromium.theme`, `helix.toml`, `icons.theme`, `shell.toml`, taustad ja eelvaated säilivad kõik. Ainult see, mis maha kukkus, genereeritakse sinu masinal uuesti failist `colors.toml`.

Arch eristab neid kahte selle järgi, kas teemal on sees oma git repositoorium, mille `archctl theme install` kloonimisel sinna jätab. Nii jääb teema, mille ise kirjutasid, sinu omaks ja teema, mille internetist tõmbasid, jääb värvideks.

### Hele režiim

Kui teed heleda režiimi teemat, sea oma faili `colors.toml` algusesse `mode = "light"`. Siis seotakse see automaatselt kõigi rakenduste heleda režiimiga. (Vana viis tühja faili nimega `light.mode` teema juure jätmisega töötab samuti edasi.)

### Ikoonide värvid

Kui tahad failihalduri ikoone oma teemaga värvi poolest sobitada, lisa fail nimega `icons.theme` koos kasutada soovitud ikoonikomplekti nimega. Vaikimisi on valikud: `Yaru Yaru-blue Yaru-dark Yaru-magenta Yaru-olive Yaru-prussiangreen Yaru-purple Yaru-red Yaru-sage Yaru-wartybrown Yaru-yellow`.

### Ava pilt

Teemad, millega tulevad kaasa pildid `unlock.png` ja `preview-unlock.png`, loetletakse jaotises _Stiil > Ava lukk_. Sinu `unlock.png` peaks eelistatult olema läbipaistev png. Ja eelvaate pildi saad luua käsuga `arch plymouth preview`.

### Selliste rakenduste teemastamine, mida Arch ei kata

Kui kasutad rakendust, mida selles loendis pole, saad Archle õpetada seda ise malliga teemastama. Pane kausta `~/.config/arch/themed/` fail, mille nimi on selle genereeritava seadistusfaili järgi koos laiendiga `.tpl`, ja kirjuta seadistus kohatäidetega `{{ background }}`, `{{ foreground }}`, `{{ accent }}`, `{{ red }}`, `{{ color0 }}` kuni `{{ color15 }}` ja ülejäänud palett. Iga kord, kui teemat vahetad, genereeritakse fail selle teema värvidega uuesti.

Samas kaustas on täielikult kommenteeritud `alacritty.toml.tpl.sample`, millest kopeerida — see loetleb iga muutuja, mida saad kasutada, pluss modifikaatorid `_strip` ja `_rgb` rakenduste jaoks, mis tahavad oma värve ilma `#`-ta või kümnend-RGB kujul. Sinu mallid on Arch enda omadest ülimuslikud, nii et saad seda kasutada ka selleks, et muuta, kuidas sisseehitatud rakendust teemastatakse.

### Oma teema levitamine

Kui tahad oma teemat levitada, et teised saaksid seda kasutada, pead selle panema avalikku git serverisse, nagu GitHub. Siis saavad inimesed selle paigaldada Arch menüüs jaotise _Paigalda > Stiil > Teema_ kaudu seda URL-i kasutades. Soovitatav on järgida nimetamistava `arch-[themename]-theme`, sest pärast paigaldamist näidatakse teemat teemavaliku menüüs õigesti lihtsalt nimega `[themename]`.

See allesjääv `[themename]` saab teema kaustanimeks, nii et see peab olema selline, mida Arch saab turvaliselt edasi anda: see peab algama tähe, numbri või allkriipsuga ja ülejäänud osa võib sisaldada tähti, numbreid, `.`, `_`, `+` ja `-`. Suurtähed teisendatakse sinu eest väiketähtedeks, aga kõik muu — tühik, jutumärk, mitte-inglise märk — lükatakse paigaldamisel tagasi, selle asemel et kaustanimeks muuta. Nii et `arch-tokyo-night-theme`, `arch-flexoki_light-theme` ja `arch-c++-theme` paigaldatakse kõik hästi.

Pea meeles, et kui see on repositooriumist paigaldatud, kukub iga koos sellega tulev `.lua`, terminali seadistus või `vscode.json` maha, nii et ära ehita teemat nende ümber.

Sa saad lasta oma teema lisada [lisateemade lehele](https://github.com/kairosci/arch/themes/) saates pull requesti [arch-site repositooriumisse](https://github.com/kairosci/arch).
