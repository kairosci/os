# Ažuriranja

Arch i tvoji paketi održavaju se ažurnima putem _Ažuriraj > Arch_ u izborniku Arch (`Super + Space`).

Sam Arch instaliran je kao redovni pacman paketi iz [Arch Package Repository](https://github.com/kairosci/arch), pa ažuriranje instalira [najnovije Arch izdanje](https://github.com/kairosci/arch), pokreće sve migracije na čekanju kako bi tvoj sustav uskladio s najnovijim i ažurira sve pakete sustava iz [Arch Arch Mirror](https://github.com/kairosci/arch) i [AUR](https://aur.archlinux.org/) (ako imaš instalirane bilo kakve AUR pakete).

Kad se objave nova izdanja, ikona kružne strelice pojavit će se desno od tvog sata. Klikni je i proces ažuriranja će započeti.

![update-available](images/update-available.webp)

### Četiri kanala

Arch se ažurira duž četiri kanala: stable, RC, edge i dev. Nove instalacije počinju na kanalu stable, koji prati [službena izdanja](https://github.com/kairosci/arch), kao i [stabilno Arch Arch zrcalo](https://github.com/kairosci/arch) koje zaostaje mjesec dana za najnovijim, kako bismo mogli uhvatiti sve nove nekompatibilnosti koje zahtijevaju promjene konfiguracije prije nego što ljudima uzrokuju probleme.

Ali ako želiš pomoći u uočavanju tih potencijalnih problema, možeš koristiti kanal edge. To će tvoje Arch pakete držati u praćenju najnovijih razvojnih buildova i omogućuje ti ažuriranje na najnovije Arch pakete čim budu dostupni. Ovo bi trebao raditi samo ako si iskusan s Linuxom i znaš kako oporaviti sustav koji ima probleme.

Prije svakog novog glavnog izdanja, radit ćemo završnu validaciju koristeći kanal RC. Ako te zanima pomoć sa završnim poliranjem, dođi visjeti u #arch-release-candidates na Discordu.

Na kraju, tu je kanal dev, koji Arch povezuje izravno s git checkoutom izvornog koda u `~/arch`, u kombinaciji s paketima edge. Ovaj kanal trebao bi koristiti samo ako si iskusan korisnik Linuxa, radiš izravno na Archju i spreman si tolerirati kvarove.

Između kanala možeš prebacivati koristeći _Ažuriraj > Channel_ iz izbornika Arch (ili `arch-channel-set` u terminalu).

### Ažuriranja firmwarea

Tvoji paketi nisu jedina stvar koja zastarijeva. Mnogi prijenosnici i periferni uređaji isporučuju BIOS, SSD i firmware docka putem Linux Vendor Firmware Service, a _Ažuriraj > Firmware_ u izborniku Arch dohvatit će i instalirati sve što tvoj hardver čeka. Instalira `fwupd` prvi put kad ga pokreneš. Mnogo firmwarea može se zapisati samo tijekom ponovnog pokretanja, pa se nemoj iznenaditi ako te zatraži jedno.

### Upozorenje o izravnim ažuriranjima pacman/yay

Ako si već upoznat s Archom, možda ćeš biti u iskušenju da samo sam pokreneš `pacman -Syu` ili `yay -Syu`, ali ako to učiniš, propustit ćeš snapshot, migracije i ažuriranja konfiguracije koje Arch pokreće zajedno s novim paketima. Zato će Arch zapravo zaustaviti izravnu nadogradnju sustava i uputiti te na `archctl update` umjesto toga. (Ako stvarno znaš što radiš, stražar će ti reći kako ga zaobići za jednu transakciju.)

### Vraćanje loših ažuriranja

Ako ikada imaš problem nakon ažuriranja, možeš vratiti sustav na snapshot snimljen prije ažuriranja. Samo ponovno pokreni i odaberi snapshot u izborniku za pokretanje od prije početka ažuriranja.

![bootloader](images/bootloader.webp)

Ako su nekako tvoje konfiguracijske datoteke oštećene, možeš izvršiti i ponovnu instalaciju Archja koristeći `arch reinstall` u terminalu. To će ponovno instalirati sve zadane Arch pakete, postaviti te na stable i downgradirati sve pakete koji su previše novi te resetirati sve konfiguracijske datoteke. Imaj na umu da će sve tvoje korisničke promjene konfiguracije u odnosu na Arch zadane postavke ovime biti prebrisane!
