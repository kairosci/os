# Posodobitve

Arch in vaši paketi se posodabljajo prek _Posodobi > Arch_ v meniju Arch (`Super + Space`).

Sam Arch je nameščen kot običajen paket pacman iz [repozitorija paketov Arch](https://github.com/kairosci/arch), tako da posodobitev namesti [najnovejšo izdajo Arch](https://github.com/kairosci/arch), izvede vse čakajoče migracije, da vaš sistem uskladi z najnovejšim, in posodobi vse sistemske pakete iz [ogledala Arch Arch Mirror](https://github.com/kairosci/arch) in [AUR](https://aur.archlinux.org/) (če ste namestili kakšne pakete AUR).

Ko so izdelane nove izdaje, se desno od vaše ure prikaže ikona krožne puščice. Kliknite jo in postopek posodobitve se bo začel.

![update-available](images/update-available.webp)

### Štiri kanali

Arch se posodablja po štirih kanalih: stable, RC, edge in dev. Nove namestitve se začnejo na kanalu stable, ki sledi [uradnim izdajam](https://github.com/kairosci/arch), ter [stabilnemu ogledalu Arch Arch](https://github.com/kairosci/arch), ki teče en mesec za najnovejšim, tako da lahko ujamemo morebitne nove nezdružljivosti, ki zahtevajo spremembe konfiguracije, preden ljudem povzročijo težave.

Če pa želite pomagati prepoznati te morebitne težave, lahko tečete na kanalu edge. To bo vaše pakete Arch ohranjalo na najnovejših razvojnih zgradbah in vam omogoča posodobitev na najnovejše pakete Arch takoj, ko so na voljo. To počnite le, če imate izkušnje z Linuxom in veste, kako obnoviti sistem, ki ima težave.

Pred vsako novo veliko izdajo bomo opravili končno preverjanje prek kanala RC. Če želite pomagati pri končnem poliranju, pridite v #arch-release-candidates na Discordu.

Nazadnje je tu kanal dev, ki Arch neposredno poveže s kopijo izvorne kode git v `~/arch` v kombinaciji s paketi edge. Ta kanal uporabite le, če ste izkušen uporabnik Linuxa, delate neposredno na Archju in ste pripravljeni prenašati okvare.

Med kanali lahko preklapljate z _Posodobi > Kanal_ iz menija Arch (ali `arch-channel-set` v terminalu).

### Posodobitve vdelane programske opreme

Vaši paketi niso edina stvar, ki zastara. Številni prenosniki in zunanje naprave dobavljajo vdelano programsko opremo BIOS, SSD in priklopnih postaj prek Linux Vendor Firmware Service in _Posodobi > Vdelana programska oprema_ v meniju Arch bo prinesla in namestila, kar koli čaka vašo strojno opremo. Ob prvem zagonu namesti `fwupd`. Veliko vdelane programske opreme je mogoče zapisati le med ponovnim zagonom, zato se ne čudite, če vas vpraša po njem.

### Opozorilo o neposrednih posodobitvah pacman/yay

Če Arch že poznate, bi vas lahko zamikalo, da bi sami preprosto zagnali `pacman -Syu` ali `yay -Syu`, vendar boste, če to storite, zamudili posnetek, migracije in posodobitve konfiguracije, ki jih Arch izvaja skupaj z novimi paketi. Zato bo Arch dejansko ustavil neposredno nadgradnjo sistema in vas usmeril na `archctl update`. (Če res veste, kaj počnete, vam bo varovalo povedalo, kako ga zaobiti za eno samo transakcijo.)

### Vračanje slabih posodobitev

Če boste imeli kadar koli težavo po posodobitvi, lahko sistem vrnete na posnetek, zajet pred posodobitvijo. Samo znova zaženite in v zagonskem meniju izberite posnetek iz časa pred začetkom posodobitve.

![bootloader](images/bootloader.webp)

Če so vaše konfiguracijske datoteke nekako poškodovane, lahko izvedete tudi ponovno namestitev Arch z `arch reinstall` v terminalu. To bo ponovno namestilo vse privzete pakete Arch, vas postavilo na stable in znižalo vse pakete, ki so prenevi, ter ponastavilo vse konfiguracijske datoteke. Upoštevajte, da bodo vse vaše spremembe uporabniških konfiguracij privzetih vrednosti Arch pri tem prepisane!
