# Navigáció

Az Archban minden billentyűzetről történik — _MINDEN!_ Amikor a rendszer először elindul, szó szerint semmit nem tudsz csinálni csak az egérrel. De megnyomhatod a `Super + Space` billentyűket, hogy előhívd az Arch menüt, és innen szinte mindent meg tudsz csinálni.

De az Arch menü nem is arra van szánva, hogy legtöbbször ezen keresztül működd a rendszert. Ennél gyorsabbak is tudunk lenni! Az összes legfontosabb alkalmazás közvetlenül egyes billentyűkombinációkhoz van kötve. A terminált a `Super + Return`, a böngészőt a `Super + Shift + Return` billentyűkkel indítod. Próbáld ki az egyiket a másik után, és meglátod a Hyprland csempézésének varázsát működés közben:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Ezután megnyomhatod a `Super + J` billentyűket, hogy egymás fölé rakd őket, ahelyett hogy egymás mellett lennének:

 ![navigation-stacked](images/navigation-stacked.webp)

Nyomd meg újra a `Super + J` billentyűket, hogy visszaálljanak az egymás melletti pozíciójukba. Ezután, amíg a böngészőn vagy, próbáld ki a `Super + Shift + Arrow Right` billentyűket az ablakok felcseréléséhez.

Most próbáld ki a `Super + Ctrl + T` billentyűket az Activity monitor indításához. Ez lebegő ablakként fog megjelenni. Csempézheted a `Super + T` segítségével (és nyomd meg újra, hogy ismét lebegő legyen). Most nyomd meg a `Super + Shift + F` billentyűket a fájlkezelő megnyitásához. Szép négyirányú elrendezésed lesz:

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

A `Super + Arrow` billentyűkkel navigálsz az aktívvá tenni kívánt ablakok között. Ez átváltja a fókuszt, és a kurzort az új alkalmazás közepére mozgatja.

Ha megnyomod a `Super + Shift + 2` billentyűket, az éppen fókuszált alkalmazást a második munkaterületre mozgatod. A `Super + Shift + 1` visszamozgatja. (És a `Super + Shift + Alt + 2` az éppen fókuszált alkalmazást a második munkaterületre mozgatja anélkül, hogy átváltana rá).

Ha lenyomva tartod a `Super` billentyűt, és az egérrel egy ablakra kattintasz, át tudod rendezni, hol helyezkedjen el. Ha lenyomva tartod a `Super` billentyűt, és az egér jobb gombját használod, szabadon átméretezheted az ablakot.

Egy ablakot a `Super + W` vagy a `Super + Q` billentyűkkel zársz be (és az összes ablakot a `Ctrl + Alt + Delete` billentyűkkel).

Teljes képernyőre is válthatsz a `Super + F` billentyűkkel, vagy akár csak teljes szélességűre (a felső sáv megtartásával) a `Super + Alt + F` billentyűkkel, vagy teljes képernyőre egy ablakon belül a `Super + Ctrl + F` billentyűkkel (YouTube-hoz jó!).

### Dwindle vagy scrolling elrendezés

Az Arch alapértelmezett elrendezését dwindle-nek hívják. Minden ablakot, amit egyetlen munkaterületen megnyitottál, mindig láthatóan tart, még akkor is, ha össze kell zsugorítania őket.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

De azt is választhatod, hogy egy munkaterületet scrolling elrendezéssé alakítasz, ahol az ablakok egymás mellett sorakoznak, túl a kijelző látható szélén. Egyetlen munkaterületet a `Super + L` billentyűkkel alakíthatsz át ebbe az elrendezésbe.

A `Super + L` ismételt megnyomása lebegővé teszi a munkaterületet, ahol az ablakok szabadon átfedik egymást, és magad helyezed el őket, egy harmadik megnyomás pedig visszaállítja dwindle-re. A `Super + Alt + L` a másik irányban megy végig rajtuk. Egy ablak, amely amúgy is lebeg — egy, amelyet a `Super + T` billentyűkkel emeltél ki, vagy egy alkalmazás, amely mindig lebegőként nyílik meg — lebegő marad, amikor a munkaterület visszatér a csempézéshez. A felső sáv azt a munkaterületet, amelyen vagy, az elrendezésével jelöli: négyzet a dwindle, kör a scrolling, és háromszög a lebegő esetén. Erre a jelre kattintva szintén váltogathatod az elrendezést.

 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

A választás munkaterületenként értendő, és megmarad. Így az 1. munkaterületet dwindle-en tarthatod böngészéshez, a 2. munkaterületet scrollingon kódoláshoz, és újraindítás után is így térnek vissza.

Ha a scrolling elrendezést szeretnéd alapértelmezettként használni, azt a `~/.config/hypr/looknfeel.lua` fájlban állíthatod be:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Ablakok csoportosítása

Az ablakok a `Super + G` billentyűkkel csoportosíthatók. Amint egy csoportban vagy, minden ablak, amelyet amíg ez aktív, elindítasz, a csoporthoz fog tartozni. Ezek között a csoportosított ablakok között a `Super + Ctrl + Arrow Left/Right` billentyűkkel léphetsz, vagy a `Super + Alt + 1/2/3/4` billentyűkkel közvetlenül a sorrendben lévő csoportosított ablakhoz ugorhatsz.

Egy ablakot a `Super + Alt + G` billentyűkkel vehetsz ki a csoportosításból, vagy a `Super + G` ismételt megnyomásával felbonthatod az egész csoportot. Végül a csoporton kívül lévő ablakokat a `Super + Alt + Arrows` billentyűkkel mozgathatod be a csoportba.

### Scratchpad munkaterület

Végül van egy speciális scratchpad munkaterület, amely lenyílik bármelyik munkaterület fölé, amelyen éppen vagy, hasonlóan egy Quake konzolhoz. A `Super + Grave` vagy a `Super + S` billentyűkkel kapcsolhatod be és ki, és a `Super + Shift + Grave` vagy a `Super + Alt + S` billentyűkkel helyezhetsz oda egy ablakot.

Különösen jól működik egy agentet futtató terminálhoz, vagy olyan vezérlőkhöz, amelyekkel gyorsan akarsz interakcióba lépni anélkül, hogy elhagynád a jelenlegi munkaterületet. Ahhoz, hogy egy ablakot levegyél a scratchpadről, küldd közvetlenül egy másik munkaterületre valamivel, mint például a `Super + Shift + 1`.

Amíg a scratchpad egyetlen ablakot tart, középre igazított panelként nyílik le, ahelyett hogy átérné a képernyőt. Tegyél rá egy második alkalmazást, és visszatér teljes szélességűre, így a kettőnek van helye egymás mellett ülni.

### Kell egy kis megszokás!

Kell egy kis idő, amíg megszokod, hogy így navigálsz az asztalodon, de amint megteszed, nehéz lesz visszatérni egy hagyományos, egérrel vezérelt asztali élményhez!
