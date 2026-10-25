# Prekės ženklas

Arch leidžia nustatyti savo įmonės logotipą ar asmeninį paveikslėlį ir įkrovos atrakinimui, ir ekrano užsklandai, ir apie ekranui.

### Įkrovos atrakinimas

Gali naudoti `arch plymouth preview`, kad pamatytum, kaip atrodytų tavo pasirinktinis logotipas ir spalvos. Jis priima fono spalvą, teksto spalvą, logotipo png ir peržiūros paveikslėlio kelią:

```
arch plymouth preview '#1d2021' '#ebdbb2' logo.png preview.png
```

Tada pritaikyk sąranką su `arch plymouth set '#1d2021' '#ebdbb2' logo.png` — tai SDDM prisijungimo ekranui taip pat duos tas pačias spalvas ir logotipą. Jei nori grąžinti, gali naudoti `arch plymouth reset`.

 ![branding-plymouth-shopify](images/branding-plymouth-shopify.webp)

### Ekrano užsklanda

Ekrano užsklandai naudojamą logotipą gali keisti po _Stilius > Ekrano užsklanda_. Tai ASCII logotipas, todėl tekstą gali redaguoti tiesiogiai, bet gali jam duoti ir png arba svg paveikslėlį, ir mes jį paversime į ASCII. Atrodo visai šauniai.

 ![branding-screensaver](images/branding-screensaver.webp)

Tame meniu yra trys įrašai:

- **Redaguoti tekstą** atidaro `~/.config/arch/branding/screensaver.txt` tavo redaktoriuje. Įrašyk ar įklijuok ką nori — ASCII meną, savo vardą, nepadorų žodį. Išsaugok ir išeik, ir ekrano užsklanda iškart įsijungs, kad galėtum pamatyti.
- **Nustatyti iš paveikslėlio** atidaro failų parinkiklį png arba svg, paverčia jį į ASCII ir parodo rezultatą. Logotipai su aiškiu siluetu veikia daug geriau nei nuotraukos.
- **Atkurti numatytąjį** grąžina Arch logotipą.

### Apie ekranas

Tos pačios trys parinktys yra po _Stilius > Apie_ ekranui _Apie_, kurį gauni iš Arch meniu, ir jos veikia identiškai — failas yra `~/.config/arch/branding/about.txt`, o langas Apie iššoka po kiekvieno pakeitimo. Apie menas konvertuojamas į mažesnį dydį nei ekrano užsklandos, nes jis turi tilpti lange, užuot užpildęs ekraną.

Kol langas atvertas, žalias blyksnis kas kelias sekundes palinksta per meną ir tada vėl jį palieka ramų. Tavo menas jį taip pat gauna, kol kiekvienas jo simbolis yra vieno stulpelio pločio — viskas, ką pagamina _Nustatyti iš paveikslėlio_, toks yra. Menas, sukurtas iš emoji arba dvigubo pločio simbolių, vietoj to lieka ramus, ir taip pat ekranas, jei laikai savą fastfetch konfigūraciją: ramus logotipas tais atvejais yra animacija, kuri nesimaišo po kojomis, o ne gedimas, nes blyksnis, slenkantis per juos, likusią eilutės dalį numestų ne į tą vietą.

 ![branding-about](images/branding-about.webp)

### Paveikslėlių konvertavimas pačiam

Abi _Nustatyti iš paveikslėlio_ parinktys tiesiog kviečia `arch transcode ascii`, kurį gali paleisti tiesiogiai, jei nori valdyti konvertavimą:

```
arch transcode ascii ~/logo.svg ~/.config/arch/branding/screensaver.txt --width 100
```

Jis priima `--width` ir `--height` terminalo stulpeliais ir eilutėmis, `--mode` — `braille` (numatytąjį ir daug smulkesnį) arba `block`, `--threshold` procentą, sprendžiantį, kurie pikseliai skaičiuojasi kaip logotipo dalis, ir `--invert` tam atvejui, kai tavo logotipas šviesus tamsiame fone. Jei konvertavimas išeina gumbuotas, slenkstis paprastai yra ta rankenėlė, kurią verta pasukti.

### Žodžiai vietoj logotipo

`archctl ascii` piešia tekstą Delta Corps Priest 1 — FIGlet šriftu, kuriuo nupieštas pats Arch žodinis ženklas, todėl ekrano užsklanda gali ką nors sakyti, užuot rodžiusi paveikslėlį:

```
archctl ascii "Back in five" > ~/.config/arch/branding/screensaver.txt
```

Jis priima tekstą kaip argumentus arba skaito jį iš vamzdžio, kai argumentų neduodama. Šriftas turi tik raides ir tarpus — jis buvo nupieštas be skaitmenų ir skyrybos — todėl visa kita išmetama ir įvardijama stderr, užuot tyliai praryta.
