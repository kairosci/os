# Shell-lisäosat

Arch-työpöytä toimii yhtenä pitkään elävänä Quickshell-prosessina nimeltä `arch-shell`, ja melkein kaikki, mitä näet näytöllä, on lisäosa sen sisällä. Palkki on lisäosa. Niin ovat myös siitä putoavat paneelit, koko näytön peitteet, kuten emoji-valitsin ja leikepöydän hallinta, itse Arch-valikko, lukitusnäyttö, polkit-valintaikkuna ja päättömät palvelut, jotka tarkkailevat akkuasi ja lämmittävät näyttöäsi yöllä.

Se ei ole vain toteutuksen yksityiskohta. Se tarkoittaa, että voit kytkeä työpöydän osia pois päältä, vaihtaa niitä tai kirjoittaa omia koskematta riviäkään Archn lähdekoodia.

Ensimmäisen osapuolen lisäosat toimitetaan Archn mukana ja sijaitsevat hakemistossa `$ARCH_PATH/src/shell/plugins/`. Kaikki, mitä lisäät itse — omat kokeilusi tai jotain GitHubista löytämääsi — sijaitsee hakemistossa `~/.config/arch/plugins/`. Molemmat löydetään samalla tavalla käynnistyksen yhteydessä, mutta sisäänrakennetut saavat luotettuja shell-rajapintoja, kun taas kolmannen osapuolen lisäosat saavat rajoitetun rajapinnan, joka on rajattu niiden omaan palveluun ja elinkaareen. Sisäänrakennettujen kloonit säilyttävät vain lähdekohtaisen määrityksen ja käyttökutsut, joita alkuperäinen käyttäytyminen tarvitsee.

## Sen näkeminen, mitä sinulla on

```
arch plugin list
```

Se tulostaa jokaisen löydetyn lisäosan id:ineen, sen, onko se käytössä, sen, onko se ensimmäisen vai kolmannen osapuolen, sen lajit ja sen näyttönimen. Lisää `--json`, jos syötät sitä jollekin muulle.

Lisäosien id:t ovat nimiavaruudella varustettuja. Sisäänrakennetut alkavat kaikki etuliitteellä `arch.` — `arch.clock`, `arch.network`, `arch.notifications` — ja tuo nimiavaruus on varattu, joten kolmannen osapuolen lisäosa ei voi koskaan vaatia sitä.

## Niiden kytkeminen päälle ja pois

```
arch plugin enable arch.tailscale
arch plugin disable arch.weather
```

Tai käytä valikkoa: _Asetukset > Plugins_:ssä on Enable, Disable, Add, Clone ja Remove, jokaisessa valitsin, joka tarjoaa vain ne lisäosat, jotka sopivat kyseiseen toimintaan.

Käytössäolotila tallennetaan tiedostoon `~/.config/arch/shell.json`, ja sääntö eroaa hieman kahden lisäosalajin osalta. Kolmannen osapuolen lisäosa on käytössä täsmälleen silloin, kun sen id esiintyy jossain tuossa tiedostossa — palkin asettelumerkintänä, merkintänä listassa `plugins[]` tai merkintänä `bar.id`. Ensimmäisen osapuolen lisäosat, jotka eivät ole palkin widgettejä, ovat toisin päin: ne ovat oletuksena päällä ja kytkeytyvät pois vain olemalla listassa `disabledPlugins[]`.

Täydellä palkin lisäosalla ei ole lainkaan pois-tilaa. Palkkeja on aina täsmälleen yksi, joten korvaat sen ottamalla käyttöön toisen. Palkin widgettien sijoittelu käsitellään kohdassa [yläpalkki](05-the-top-bar.md).

## Lisäosan lisääminen gitistä

Kolmannen osapuolen lisäosa on vain git-repo, jonka juuressa on tiedosto `manifest.json`.

```
arch plugin add https://github.com/acme/arch-weather.git --enable
```

Ennen kuin se tekee mitään, se kertoo sinulle selkeästi, että lisäosat toimivat mielivaltaisena, hiekkalaatikoimattomana koodina pitkään elävän shell-prosessisi sisällä, näyttää sinulle URL:n ja pyytää sinua vahvistamaan. Ota se vakavasti. Kolmannen osapuolen lisäosarajapinta ei suoraan paljasta todennuspalveluja, ja korvaava palkki saa vain rajoitettuja kykyjä määritellylle ei-todennuskäyttöliittymälle. Visuaaliset lisäosat jakavat silti shellin QML-näkymän ja voivat kulkea tavallisten yläobjektien kautta, kun taas kaikki lisäosakoodi toimii kaiken sen kanssa, minkä käyttäjätilisi voi tavoittaa. Todennustila suojataan erikseen pitämällä nuo palvelut tavoitettavan isäntäobjektigraafin ulkopuolella. Lisää vain repoja, joita olet valmis ajamaan, ja lue ne ennen kuin otat ne käyttöön.

Korvaava palkki voi hahmontaa asennettuja widgettejä, mutta palveluun nojaavilla kolmannen osapuolen widgeteillä voi siellä olla rajoitettua toiminnallisuutta, koska palkki ei saa pyytää toisen lisäosan elävää palveluobjektia. Vaihda takaisin sisäänrakennettuun `arch.bar`-palkkiin, jos sellainen widgetti tarvitsee kumppanipalveluaan.

Sitten se kloonaa repon vaihehakemistoon, validoi manifestin, kieltää asennuksen, jos toinen lisäosa jo vaatii tuon id:n, ja siirtää sen hakemistoon `~/.config/arch/plugins/<id>/`. Ilman valitsinta `--enable` se kysyy, haluatko sen päälle nyt, ja voit sanoa ei ja mennä lukemaan koodia ensin. Se ei koskaan aja mitään lisäosasta, ei koskaan suorita asennuskoukkua eikä koskaan pyydä sudoa — se kloonaa tiedostoja, tarkistaa manifestin ja kääntää bitin IPC:n yli.

Päivittäminen on saman noudetun kopion pikaeteenpäin-veto:

```
arch plugin update acme.weather
arch plugin update
```

Ilman id:tä se päivittää jokaisen git-hallinnoidun lisäosasi. Se näyttää sinulle diffin ennen sen soveltamista, kieltäytyy päivittämästä, jos sinulla on paikallisia muutoksia, joista se ei voi pikaedetä ohi, ja palauttaa, jos uusi revisio epäonnistuu validoinnissa.

```
arch plugin remove acme.weather
```

Poisto kytkee lisäosan ensin pois käytöstä ja poistaa sen sitten, jos se on git-noudettu kopio (repo on edelleen ylävirrassa), tai irrottaa sen linkityksen, jos se on symbolinen linkki. Käsin tehty lisäosakansio, jossa ei ole git-repoa, siirretään aikaleimattuun varmuuskopioon lisäosahakemiston sisällä sen sijaan, että se poistettaisiin suoralta kädeltä.

## Sisäänrakennetun kloonaaminen muokattavaksi

Tämä on suosikkiosani. Jos haluat muuttaa sitä, kuinka sisäänrakennettu widgetti käyttäytyy, älä muokkaa tiedostoja hakemistossa `$ARCH_PATH` — ne kuuluvat pakettiin ja seuraava päivitys ylikirjoittaa ne. Kloonaa se sen sijaan:

```
arch plugin clone arch.clock
```

Se kopioi koko lisäosan hakemistoon `~/.config/arch/plugins/dhh.clock` (sinun käyttäjänimesi, ei minun), nimeää sen uudelleen muotoon "My Clock", ottaa sen käyttöön ja vaihtaa shellin sisäänrakennetusta kopioosi — säilyttäen olemassa olevan palkin widgetin sijainnin ja asetukset. Lisää `--edit` avataksesi uuden hakemiston muuttujassa `$EDITOR` heti, minkä valikon _Asetukset > Plugins > Clone Plugin_ tekee puolestasi.

Käyttäjänimietuliite pitää kloonisi id:n sinun omasi, joten sen jakaminen ei törmää kenenkään muun kanssa. Alkuperäiselle sisäänrakennetulle id:lle tehdyt kutsut reititetään klooniisi, joten minkään, mikä viittasi tunnisteeseen `arch.clock`, ei tarvitse päivittyä. Ja jos sotket sen, `arch plugin remove dhh.clock` laittaa sisäänrakennetun takaisin.

Tiedoston tallentaminen minne tahansa hakemistossa `~/.config/arch/plugins/` lataa lisäosakoodin uudelleen automaattisesti, joten voit jättää editorin auki ja katsella muutostesi saapumista.

## Oman kirjoittaminen

Lisäosa on hakemisto, jossa on tiedosto `manifest.json` ja jonkin verran QML:ää. Manifesti julistaa `schemaVersion: 1`, kentän `id`, `name`, `version`, yhden tai useamman kentän `kinds` ja objektin `entryPoints`, joka osoittaa jokaisen lajin QML-tiedostoon:

| Laji | Mikä se on |
|------|------------|
| `bar-widget` | Komponentti, jonka aktiivinen palkki voi pudottaa osioon |
| `panel` | Pysyvä tai kutsuttu kelluva ikkuna |
| `overlay` | Koko näytön peite |
| `menu` | Kutsuttu valikkopinta |
| `service` | Päätön singleton ilman käyttöliittymää |
| `bar` | Täysi palkki, joka korvaa sisäänrakennetun |

Lisäosa voi julistaa useita lajeja kerralla — media-lisäosa on sekä `service` että `bar-widget`. Palkin widgetit saavat ylimääräisen lohkon `barWidget`, jossa on näyttönimi, luokka, valinnainen `defaultSection` ja `allowMultiple`, joka kertoo, onko järkevää olla useampaa kuin yksi palkissa. Useimmat widgetit asettavat sen arvoon `false`; välikkeet ja ilmaisimet asettavat sen arvoon `true`.

Ennen kuin julkaiset mitään, tarkista se:

```
arch plugin validate ./my-plugin
```

Se ajaa samat tarkistukset, jotka shell tekee latausaikana: skeemaversion, vaaditut kentät, id:n, joka ei ole varattu, aloituspisteet, jotka ovat turvallisia suhteellisia polkuja ja oikeasti olemassa, aloituspisteen jokaiselle lajille, jonka väitit, eikä symbolisia linkkejä missään kansion sisällä.

Lisäosakehitykseen katso [shell-viite](https://github.com/kairosci/arch) ja [ensimmäisen osapuolen lisäosaluettelo](https://github.com/kairosci/arch).

## Omasi jakaminen maailmalle

Kun olet tehnyt jotain, mistä pidät, laita se julkiseen git-repoon. Se on koko jakelumekanismi — kuka tahansa voi sitten ajaa `arch plugin add` URL-osoitettasi vasten ja saada sen käyntiin sekunneissa.

Auttaaksesi ihmisiä oikeasti löytämään sen, listaa se osoitteessa [plugins.github.com/kairosci/arch](https://plugins.github.com/kairosci/arch). Se on Arch-shell-lisäosien kauppapaikka, ja se on ensimmäinen paikka, josta kannattaa katsoa, kun pohdit, onko joku jo rakentanut widgetin, jota olet aikeissa kirjoittaa. Selaa sitä ennen kuin aloitat!
