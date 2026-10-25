# Navigacija

Sve se u Archju odvija putem tipkovnice — _SVE!_ Kad se sustav prvi put pokrene, doslovno ne možete učiniti ništa samo mišem. Ali možete pritisnuti `Super + Space` da prikažete Arch Menu i odavde možete učiniti gotovo sve.

Ali Arch izbornik većinu vremena čak ni nije zamišljen kao glavni način upravljanja sustavom. Možemo biti brži od toga! Sve najvažnije aplikacije izravno su vezane uz pojedinačne prečace. Terminal pokrećete sa `Super + Return`, a preglednik sa `Super + Shift + Return`. Pokušajte to učiniti jedno za drugim i vidjet ćete čaroliju Hyprlandova popločavanja na djelu:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Zatim možete pritisnuti `Super + J` da ih složite jedan na drugi umjesto jedan pokraj drugog:

 ![navigation-stacked](images/navigation-stacked.webp)

Pritisnite `Super + J` ponovno da ih vratite u položaj jedan pokraj drugog. Zatim pokušajte `Super + Shift + Arrow Right` dok ste u pregledniku da zamijenite prozore.

Sada pokušajte `Super + Ctrl + T` da pokrenete monitor aktivnosti. On će se pojaviti kao plutajući prozor. Možete ga popločati pomoću `Super + T` (i pritisnite to ponovno da opet postane plutajući). Sada pritisnite `Super + Shift + F` da otvorite upravitelj datoteka. Imat ćete uredan raspored s četiri prozora:

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Premještate se između prozora koji želite da bude aktivan pomoću `Super + Arrow`. Time će se prebaciti fokus i pokazivač će se premjestiti u središte nove aplikacije.

Ako pritisnete `Super + Shift + 2`, premjestit ćete trenutačno fokusiranu aplikaciju na drugi radni prostor. `Super + Shift + 1` premješta je natrag. (A `Super + Shift + Alt + 2` premjestit će trenutačno fokusiranu aplikaciju na drugi radni prostor bez prebacivanja na njega).

Ako držite pritisnuti `Super` i mišem kliknete na prozor, moći ćete preraspodijeliti gdje se nalazi. Ako držite `Super` i koristite desnu tipku miša, možete slobodno mijenjati veličinu prozora.

Prozor zatvarate sa `Super + W` ili `Super + Q` (a sve prozore zatvarate sa `Ctrl + Alt + Delete`).

Možete ići i na cijeli zaslon sa `Super + F` ili čak samo na cijelu širinu (zadržavajući gornju traku) sa `Super + Alt + F` ili na cijeli zaslon unutar prozora sa `Super + Ctrl + F` (odlično za YouTube!).

### Raspored dwindle u odnosu na raspored scrolling

Zadani raspored u Archju zove se dwindle. On drži sve prozore koje otvorite na jednom radnom prostoru vidljivima cijelo vrijeme, čak i ako ih mora smanjiti.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Ali možete odabrati i pretvoriti radni prostor u raspored scrolling, gdje su prozori poredani jedan pokraj drugog, izvan vidljivog ruba zaslona. Pojedini radni prostor u taj raspored pretvarate pomoću `Super + L`.

Ponovni pritisak na `Super + L` pretvara radni prostor u plutajući, gdje se prozori slobodno preklapaju i sami ih postavljate, a treći pritisak vraća ga na dwindle. `Super + Alt + L` prolazi kroz njih u suprotnom smjeru. Prozor koji ionako pluta — onaj koji ste izbacili pomoću `Super + T` ili aplikacija koja se uvijek otvara plutajuća — nastavlja plutati kad se radni prostor vrati na popločavanje. Gornja traka označava radni prostor na kojem se nalazite njegovim rasporedom: kvadrat za dwindle, krug za scrolling i trokut za plutajući. Klik na tu oznaku također ciklički mijenja raspored.

 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Odabir je po radnom prostoru i ostaje zapamćen. Tako radni prostor 1 možete držati na dwindleu za pregledavanje, a radni prostor 2 na scrollingu za kod, i vratit će se takvi nakon ponovnog pokretanja.

Ako želite koristiti raspored scrolling kao zadani, to možete postaviti u `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Grupiranje prozora

Prozore je moguće grupirati pomoću `Super + G`. Kad ste jednom u grupi, svaki prozor koji pokrenete dok je ona aktivna pripadat će grupi. Između tih grupiranih prozora možete se kretati pomoću `Super + Ctrl + Arrow Left/Right` ili `Super + Alt + 1/2/3/4` da izravno odete na grupirani prozor po redu.

Prozor možete izbaciti iz grupiranja pomoću `Super + Alt + G` ili rastaviti cijelu grupu ponovnim pritiskom na `Super + G`. Na kraju, prozore izvan grupe možete premjestiti u nju pomoću `Super + Alt + Arrows`.

### Radni prostor scratchpad

Na kraju, postoji poseban radni prostor scratchpad koji se spušta preko radnog prostora na kojem se trenutačno nalazite, poput Quake konzole. Uključujte ga i isključujte pomoću `Super + Grave` ili `Super + S`, a prozor ondje postavite pomoću `Super + Shift + Grave` ili `Super + Alt + S`.

Osobito dobro radi za terminal u kojem radi agent ili za kontrole s kojima želite brzo komunicirati bez napuštanja trenutačnog radnog prostora. Da premjestite prozor sa scratchpada, pošaljite ga izravno na drugi radni prostor s nečim poput `Super + Shift + 1`.

Dok scratchpad sadrži jedan prozor, spušta se kao centrirana ploča umjesto da se proteže preko zaslona. Postavite drugu aplikaciju na njega i vratit će se na punu širinu, tako da obje imaju prostora stajati jedna pokraj druge.

### Treba se malo naviknuti!

Treba malo vremena da se naviknete ovako kretati radnom površinom, ali kad se naviknete, teško ćete se vratiti tradicionalnom iskustvu radne površine upravljanom mišem!
