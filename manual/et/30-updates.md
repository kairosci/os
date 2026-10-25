# Uuendused

Arch ja sinu paketid hoitakse ajakohasena Arch menüü (`Super + Space`) jaotise _Uuenda > Arch_ kaudu.

Arch ise paigaldatakse tavaliste pacmani pakettidena [Arch paketirepost](https://github.com/kairosci/arch), nii et uuendus paigaldab [uusima Arch väljalaske](https://github.com/kairosci/arch), käivitab kõik ootel migratsioonid, et sinu süsteem uusimaga sünkroonida, ja uuendab kõiki süsteemipakette [Arch Archi peeglist](https://github.com/kairosci/arch) ja [AUR-st](https://aur.archlinux.org/) (kui sul on AUR-pakette paigaldatud).

Kui tehakse uusi väljalaskeid, ilmub sinu kella paremale ringnoole ikoon. Klõpsa seda ja uuendusprotsess algab.

![update-available](images/update-available.webp)

### Neli kanalit

Arch't uuendatakse nelja kanali kaudu: stable, RC, edge ja dev. Uued paigaldused alustavad stable kanalil, mis jälgib [ametlikke väljalaskeid](https://github.com/kairosci/arch) ning [stabiilset Arch Archi peeglit](https://github.com/kairosci/arch), mis on uusimast ühe kuu võrra maas, et saaksime kinni püüda kõik uued ühildamatused, mis nõuavad konfiguratsioonimuudatusi, enne kui need inimestele probleeme põhjustavad.

Kuid kui soovid aidata neid võimalikke probleeme märgata, saad töötada edge kanalil. See hoiab sinu Arch paketid uusimaid arendusversioone jälgimas ja võimaldab sul uuendada uusimatele Archi pakettidele kohe, kui need saadaval on. Seda peaksid tegema ainult siis, kui oled Linuxiga kogenud ja tead, kuidas probleemidega süsteemi taastada.

Enne iga uut suuremat väljalaset teeme lõpliku valideerimise RC kanali abil. Kui oled huvitatud lõpliku lihvimisega aitamisest, tule Discordis kanalisse #arch-release-candidates.

Lõpuks on dev kanal, mis lingib Arch otse lähtekoodi giti checkoutiga kaustas `~/arch`, koos edge pakettidega. Seda kanalit peaksid kasutama ainult siis, kui oled kogenud Linuxi kasutaja, töötad otse Arch kallal ja oled valmis purunemisi taluma.

Kanalite vahel saad vahetada Arch menüü jaotise _Uuenda > Channel_ abil (või terminalis käsuga `arch-channel-set`).

### Püsivara uuendused

Sinu paketid pole ainus, mis vananeb. Paljud sülearvutid ja välisseadmed tarnivad BIOS-i, SSD ja doki püsivara Linux Vendor Firmware Service'i kaudu ja Arch menüü jaotis _Uuenda > Firmware_ toob ja paigaldab kõik, mis sinu riistvaral ootab. Esimesel käivitamisel paigaldab see `fwupd`. Palju püsivara saab kirjutada ainult taaskäivituse ajal, nii et ära imesta, kui seda küsitakse.

### Hoiatus otse pacmani/yay uuenduste kohta

Kui oled Archiga juba tuttav, võib sul tekkida kiusatus lihtsalt ise `pacman -Syu` või `yay -Syu` käivitada, kuid kui sa seda teed, jääd ilma hetktõmmisest, migratsioonidest ja konfiguratsioonivärskendustest, mida Arch koos uute pakettidega käivitab. Seetõttu peatab Arch otsese süsteemi uuendamise ja osutab sind selle asemel käsule `archctl update`. (Kui sa tõesti tead, mida teed, ütleb valvur sulle, kuidas seda ühe tehingu puhul mööda hiilida.)

### Halbade uuenduste tagasivõtmine

Kui sul tekib pärast uuendamist probleem, saad oma süsteemi tagasi võtta enne uuendamist tehtud hetktõmmisele. Taaskäivita lihtsalt ja vali alglaadimismenüüs hetktõmmis ajast enne uuenduse alustamist.

![bootloader](images/bootloader.webp)

Kui sinu konfiguratsioonifailid on kuidagi rikutud, saad terminalis teha ka Arch uuesti paigaldamise käsuga `arch reinstall`. See paigaldab uuesti kõik Arch vaikepaketid, paneb su stable'ile ja alandab kõik liiga uued paketid ning lähtestab kõik konfiguratsioonifailid. Pane tähele, et kõik sinu kasutaja konfiguratsioonimuudatused Arch vaikeväärtustele kirjutatakse seda tehes üle!
