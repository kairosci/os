# Tekstin poiminta ja sanelu

### Tekstin poiminta

Paina `Super + Ctrl + PrtScr` valitaksesi ruudulta alueen tekstin poimintaa varten. Avoimen lähdekoodin tesseract-tekstintunnistusmalli muuntaa valinnan sitten nopeasti tekstiksi ja sijoittaa sen leikepöydälle. Sitten vain painat `Super + V` liittääksesi.

Tämä on erittäin hyödyllistä esimerkiksi poimiessasi osoitteita kuvien alatunnisteista tai puhelinnumeroita verkkosivustojen otsikoihin upotettuna.

 ![text-extraction](images/text-extraction.webp)

### Sanelu

Uusissa asennuksissa [Superwhisper](https://superwhisper.com/) on oletussanelutausta, joka käyttää pilviprosessointia ilman offline-mallien latauksia. Valitse Superwhisper tai [Voxtype](https://voxtype.io/) Arch-valikosta kohdasta _Asetukset > Oletukset > Sanelu_. Taustan valitseminen asentaa sen tarvittaessa ja tekee siitä sanelun oletuksen. Voxtype lataa englannin perusmallin, joka vie 150 Mt; vaihda mallia komennolla `voxtype setup model` ja muita asetuksia tiedostossa `~/.config/voxtype/config.toml`. Superwhisper avaa asetuksensa pilvi- tai paikallisen prosessoinnin valitsemiseksi, ja OPR pitää sovelluksen ajan tasalla.

Sanelet pitämällä pohjassa näppäintä `Right Alt` tai `F9` tai vaihtamalla tilaa yhdistelmällä `Super + Ctrl + X`, ja saneltu teksti ilmestyy kohdistettuun syöttökenttään. Nämä pikanäppäimet käyttävät valittua taustaa. Oikea Alt käynnistää sanelun myös, kun sitä käytetään muokainyhdistelmässä; käytä vasenta Alt-näppäintä niissä yhdistelmissä. Näppäimistöasetteluissa, joissa oikea Alt on AltGr, käytä näppäintä `F9` pitääksesi AltGr-näppäimen käytettävissä kirjoittamiseen.

Samat pikanäppäimet toimivat kummallakin taustalla. Valitse taustasi kohdasta Asetukset > Oletukset > Sanelu. Taustan asentaja määrittää sen ja tallentaa valinnan. Aja `archctl default dictation` nähdäksesi, mikä niistä on valittu. Valinta tallennetaan tiedostoon `~/.config/arch/defaults/dictation`. Uudet asennukset valitsevat Superwhisperin automaattisesti.

Arch lataa valitun taustan työpöytäintegraation automaattisesti. Superwhisperin määritystä ei tarvita hakemistossa `~/.config/hypr/`.

Mukautetut sidokset ja skriptit voivat käyttää komentoja `arch dictation start`, `arch dictation stop` ja `arch dictation toggle`. Valittu tausta hoitaa tallennuksen ja litteroinnin. Superwhisperin valitseminen poistaa käytöstä sen oman pidä pohjassa -pikanäppäimen ja asettaa sen oman vaihtokytkimen yhdistelmäksi `Alt + Space`, pitäen sen erillään Archn tallennusnäppäimistä. Superwhisper vaatii vähintään yhden oman tallennuspikanäppäimen, ja sen peruutuspikanäppäin pysyy käytettävissä.

Muut taustat voivat integroitua muuttamatta Archä. Tarjoa suoritettava tiedosto nimeltä `arch-dictation-<backend>` PATHissa, joka hyväksyy argumentit `start`, `stop` ja `toggle` ja palaa nopeasti, nollasta poikkeavalla tilalla epäonnistuessaan. Sen asentaja määrittää tarjoajan ja kutsuu komentoa `arch-dictation-use <backend>` onnistuneen määrityksen jälkeen. Tämä pysäyttää edellisen taustan ja tallentaa valinnan atomisesti; `stop` on onnistuttava, kun tarjoaja on joutilaana tai ei käytettävissä. Taustojen nimet käyttävät pieniä kirjaimia, numeroita ja yhdysmerkkejä. Tarjoa `arch-install-dictation-<backend>` määritystä varten; `archctl default dictation <backend>` käynnistää sen. Lisää Oletukset-valikon kohta Arch-valikkolaajennuksen avulla kutsumaan kyseistä valitsinta. Valinnainen työpöytäintegraatio voi sijaita tiedostossa `${XDG_CONFIG_HOME:-$HOME/.config}/<backend>/shortcuts.lua`.
