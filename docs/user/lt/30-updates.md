# Atnaujinimai

Arch ir tavo paketai išlaikomi naujausi per _Atnaujinti > Arch_ Arch meniu (`Super + Space`).

Pati Arch įdiegiama kaip įprastiniai pacman paketai iš [Arch Package Repository](https://github.com/kairosci/os), tad atnaujinimas įdiegia [naujausią Arch leidimą](https://github.com/kairosci/os), paleidžia visas laukiančias migracijas, kad tavo sistema būtų sinchronizuota su naujausia, ir atnaujina visus sistemos paketus iš [Arch Arch Mirror](https://github.com/kairosci/os) ir [AUR](https://aur.archlinux.org/) (jei įdiegei kokius nors AUR paketus).

Kai išleidžiami nauji leidimai, dešinėje nuo tavo laikrodžio pasirodys apskritimo rodyklės piktograma. Spustelėk ją ir atnaujinimo procesas prasidės.

![update-available](images/update-available.webp)

### Keturi kanalai

Arch atnaujinama pagal keturis kanalus: stable, RC, edge ir dev. Nauji diegimai prasideda stable kanale, kuris seka [oficialius leidimus](https://github.com/kairosci/os), taip pat [stable Arch Arch mirror](https://github.com/kairosci/os), kuris atsilieka mėnesiu nuo naujausio, kad galėtume pagauti visus naujus nesuderinamumus, reikalaujančius konfigūracijos pakeitimų, kol jie nesukėlė problemų žmonėms.

Bet jei norėtum padėti pastebėti tas galimas problemas, gali veikti edge kanale. Tai leis tavo Arch paketams sekti naujausias kūrimo versijas ir leis atnaujinti iki naujausių Arch paketų, kai tik jie prieinami. Tai turėtum daryti tik jei esi patyręs su Linux ir žinai, kaip atkurti sistemą, kuri turi problemų.

Prieš kiekvieną naują didelį leidimą, galutinį patvirtinimą atliksime naudodami RC kanalą. Jei domiesi pagalba su galutiniu blizginimu, apsilankyk #arch-release-candidates Discord'e.

Galiausiai yra dev kanalas, kuris susieja Arch tiesiogiai su šaltinio kodo git kopija `~/arch`, kartu su edge paketais. Šį kanalą turėtum naudoti tik jei esi patyręs Linux naudotojas, dirbantis tiesiai su Arch, ir pasiruošęs toleruoti lūžimus.

Tarp kanalų gali perjungti naudodamas _Atnaujinti > Channel_ iš Arch meniu (arba `arch-channel-set` terminale).

### Programinės aparatinės įrangos (firmware) atnaujinimai

Tavo paketai nėra vienintelis dalykas, kuris pasensta. Daugelis nešiojamųjų kompiuterių ir periferinių įrenginių BIOS, SSD ir dock programinę aparatinę įrangą pristato per Linux Vendor Firmware Service, o _Atnaujinti > Firmware_ Arch meniu paims ir įdiegs visa, kas laukia tavo aparatūrai. Jis įdiegia `fwupd` pirmą kartą jį paleidus. Daugelį programinės aparatinės įrangos galima įrašyti tik perkrovimo metu, tad nenustebk, jei paprašys.

### Įspėjimas dėl tiesioginių pacman/yay atnaujinimų

Jei jau esi susipažinęs su Arch, gali kilti pagunda tiesiog pačiam paleisti `pacman -Syu` arba `yay -Syu`, bet jei tai padarysi, praleisi momentinę kopiją, migracijas ir konfigūracijos atnaujinimus, kuriuos Arch paleidžia kartu su naujais paketais. Todėl Arch iš tikrųjų sustabdys tiesioginį sistemos atnaujinimą ir nukreips tave į `archctl update`. (Jei tikrai žinai, ką darai, apsauga pasakys, kaip ją apeiti vienai operacijai.)

### Blogų atnaujinimų atšaukimas

Jei po atnaujinimo kils problemų, gali atšaukti savo sistemą į momentinę kopiją, paimtą prieš atnaujinimą. Tiesiog paleisk iš naujo ir paleidimo meniu pasirink momentinę kopiją iš laikų prieš pradedant atnaujinimą.

![bootloader](images/bootloader.webp)

Jei kaip nors tavo konfigūracijos failai buvo sugadinti, taip pat gali atlikti Arch pakartotinį diegimą naudodamas `arch reinstall` terminale. Tai iš naujo įdiegs visus numatytuosius Arch paketus, nustatys tave į stable ir sugrąžins paketus, kurie per nauji, bei atkurs visus konfigūracijos failus. Atmink, kad atlikus tai visi tavo naudotojo konfigūracijos pakeitimai Arch numatytiesiems bus perrašyti!
