# Navigation

Alt i Arch sker via tastaturet — _ALT!_ Når systemet starter første gang, kan du bogstaveligt talt ikke gøre en eneste ting med musen alene. Men du kan trykke på `Super + Space` for at vise Arch-menuen, og herfra kan du gøre stort set alt.

Men Arch-menuen er ikke engang tænkt som den primære måde at betjene systemet på det meste af tiden. Vi kan gøre det hurtigere end det! Alle de vigtigste applikationer er bundet direkte til individuelle genvejstaster. Du starter terminalen med `Super + Return` og en browser med `Super + Shift + Return`. Prøv at gøre det ene efter det andet, så ser du magien ved Hyprlands tiling i aktion:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Du kan derefter trykke på `Super + J` for at stable dem oven på hinanden i stedet for side om side:

 ![navigation-stacked](images/navigation-stacked.webp)

Tryk på `Super + J` igen for at bringe dem tilbage til deres positioner side om side. Prøv derefter `Super + Shift + Arrow Right`, mens du er på browseren, for at bytte rundt på vinduerne.



 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Du navigerer mellem det vindue, du vil have aktivt, med `Super + Arrow`. Det skifter fokus og flytter markøren til midten af den nye applikation.

Hvis du trykker på `Super + Shift + 2`, flytter du den aktuelt fokuserede applikation til det andet arbejdsområde. `Super + Shift + 1` flytter den tilbage. (Og `Super + Shift + Alt + 2` flytter den aktuelt fokuserede applikation til det andet arbejdsområde uden at skifte til det).

Hvis du holder `Super` nede og bruger musen til at klikke på et vindue, kan du omarrangere, hvor det sidder. Hvis du holder `Super` nede og bruger højre museknap, kan du frit ændre vinduets størrelse.

Du lukker et vindue med `Super + W` eller `Super + Q` (og lukker alle vinduer med `Ctrl + Alt + Delete`).

Du kan også gå i fuld skærm med `Super + F` eller endda bare fuld bredde (med den øverste bar bevaret) med `Super + Alt + F` eller fuld skærm inden i et vindue med `Super + Ctrl + F` (godt til YouTube!).

### Dwindle vs. scrolling-layout

Archs standardlayout hedder dwindle. Det holder alle de vinduer, du åbner på et enkelt arbejdsområde, synlige hele tiden, også selvom det må krympe dem.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Men du kan også vælge at gøre et arbejdsområde til scrolling-layoutet, hvor vinduer er stillet op side om side, ud over skærmens synlige kant. Du gør et enkelt arbejdsområde til dette layout via `Super + L`.


 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Valget gælder pr. arbejdsområde, og det bliver hængende. Så du kan beholde arbejdsområde 1 på dwindle til browsing og arbejdsområde 2 på scrolling til kode, og de kommer tilbage på den måde efter en genstart.

Hvis du vil bruge scrolling-layoutet som standard, kan du indstille det i `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Gruppering af vinduer

Vinduer kan grupperes med `Super + G`. Når du er i en gruppe, vil hvert vindue, du starter, mens den er aktiv, tilhøre gruppen. Du kan flytte mellem disse grupperede vinduer med `Super + Ctrl + Arrow Left/Right` eller `Super + Alt + 1/2/3/4` for at gå direkte til et grupperet vindue i rækkefølge.

Du kan flytte et vindue ud af grupperingen med `Super + Alt + G` eller opløse hele gruppen ved at trykke på `Super + G` igen. Endelig kan du flytte vinduer uden for gruppen ind i den med `Super + Alt + Arrows`.

### Scratchpad-arbejdsområde

Til sidst er der et særligt scratchpad-arbejdsområde, der falder ned over det arbejdsområde, du aktuelt er på, meget ligesom en Quake-konsol. Slå det til og fra med `Super + Grave` eller `Super + S`, og placér et vindue der med `Super + Shift + Grave` eller `Super + Alt + S`.

Det fungerer særligt godt til en terminal, der kører en agent, eller til kontrolelementer, du vil interagere hurtigt med uden at forlade det aktuelle arbejdsområde. For at flytte et vindue væk fra scratchpadden skal du sende det direkte til et andet arbejdsområde med noget som `Super + Shift + 1`.

Mens scratchpadden indeholder et enkelt vindue, falder den ned som et centreret panel i stedet for at spænde over skærmen. Sæt en anden app på den, så går den tilbage til fuld bredde, så de to har plads til at sidde side om side.

### Det kræver lidt tilvænning!

Det tager lidt tid at vænne sig til at navigere på dit skrivebord på denne måde, men når du først gør det, bliver det svært at gå tilbage til en traditionel musdrevet skrivebordsoplevelse!
