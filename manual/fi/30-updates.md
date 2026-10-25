# Päivitykset

Arch ja pakettisi pidetään ajan tasalla Arch-valikon (`Super + Space`) kohdan _Päivitä > Arch_ kautta.

Itse Arch asennetaan tavallisina pacman-paketteina [Arch Package Repositorysta](https://github.com/kairosci/arch), joten päivitys asentaa [uusimman Arch-julkaisun](https://github.com/kairosci/arch), ajaa odottavat migraatiot saadakseen järjestelmäsi synkroniin uusimman kanssa ja päivittää kaikki järjestelmäpaketit lähteistä [Arch Arch Mirror](https://github.com/kairosci/arch) ja [AUR](https://aur.archlinux.org/) (jos olet asentanut AUR-paketteja).

Kun uusia julkaisuja tehdään, kellosi oikealle puolelle ilmestyy ympyränuolikuvake. Napsauta sitä, niin päivitysprosessi käynnistyy.

![update-available](images/update-available.webp)

### Neljä kanavaa

Archa päivitetään neljällä kanavalla: stable, RC, edge ja dev. Uudet asennukset alkavat stable-kanavalla, joka seuraa [virallisia julkaisuja](https://github.com/kairosci/arch) sekä [vakaata Arch Arch -peiliä](https://github.com/kairosci/arch), joka kulkee kuukauden uusinta jäljessä, jotta voimme saada kiinni mahdolliset uudet yhteensopimattomuudet, jotka vaativat määritysmuutoksia, ennen kuin ne aiheuttavat ihmisille ongelmia.

Mutta jos haluat auttaa havaitsemaan nuo mahdolliset ongelmat, voit toimia edge-kanavalla. Se pitää Arch-pakettisi uusimpien kehityskoontiversioiden mukana ja antaa sinun päivittää uusimpiin Arch-paketteihin heti, kun ne ovat saatavilla. Tee tämä vain, jos olet kokenut Linuxin kanssa ja tiedät, kuinka palautetaan järjestelmä, jossa on ongelmia.

Ennen jokaista uutta suurta julkaisua teemme lopullisen validoinnin RC-kanavalla. Jos olet kiinnostunut auttamaan lopullisessa hiomisessa, tule viettämään aikaa kanavalle #arch-release-candidates Discordissa.

Lopuksi on dev-kanava, joka linkittää Archn suoraan lähdekoodin git-noudettuun kopioon hakemistossa `~/arch`, yhdistettynä edge-paketteihin. Käytä tätä kanavaa vain, jos olet kokenut Linux-käyttäjä, työskentelet suoraan Archn parissa ja olet valmis sietämään rikkoutumista.

Voit vaihtaa kanavien välillä Arch-valikon kohdassa _Päivitä > Kanava_ (tai päätteessä komennolla `arch-channel-set`).

### Firmware-päivitykset

Pakettisi eivät ole ainoa asia, joka vanhenee. Monet kannettavat ja oheislaitteet toimittavat BIOS-, SSD- ja telakka-firmwarea Linux Vendor Firmware Servicen kautta, ja Arch-valikon _Päivitä > Firmware_ noutaa ja asentaa sen, mitä laitteistollasi on odottamassa. Se asentaa paketin `fwupd` ensimmäisellä ajokerralla. Paljon firmwarea voidaan kirjoittaa vain uudelleenkäynnistyksen aikana, joten älä ylläty, jos sinulta pyydetään sellaista.

### Varoitus suorista pacman/yay-päivityksistä

Jos tunnet Archin jo, saatat houkutella vain ajamaan `pacman -Syu` tai `yay -Syu` itse, mutta jos teet niin, menetät tilannekuvan, migraatiot ja määrityspäivitykset, jotka Arch ajaa yhdessä uusien pakettien kanssa. Siksi Arch oikeasti pysäyttää suoran järjestelmäpäivityksen ja osoittaa sinut sen sijaan komennolle `archctl update`. (Jos oikeasti tiedät, mitä olet tekemässä, vartija kertoo sinulle, kuinka se ohitetaan yhtä transaktiota varten.)

### Huonojen päivitysten palauttaminen

Jos sinulla on joskus ongelma päivityksen tekemisen jälkeen, voit palauttaa järjestelmäsi ennen päivitystä otettuun tilannekuvaan. Käynnistä vain uudelleen ja valitse käynnistyksen latausvalikosta tilannekuva ajalta ennen päivityksen aloittamista.

![bootloader](images/bootloader.webp)

Jos määritystiedostosi ovat jotenkin vioittuneet, voit myös suorittaa Archn uudelleenasennuksen käyttämällä päätteessä komentoa `arch reinstall`. Tämä asentaa uudelleen kaikki Archn oletuspaketit, laittaa sinut stablelle ja alentaa paketit, jotka ovat liian uusia, sekä palauttaa kaikki määritystiedostot. Huomaa, että kaikki käyttäjän määritysmuutoksesi Archn oletuksiin ylikirjoitetaan tätä tehdessäsi!
