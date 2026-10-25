# Navigazione

Tutto in Arch avviene tramite la tastiera — _TUTTO!_ Quando il sistema si avvia per la prima volta, letteralmente non puoi fare nulla con il solo mouse. Ma puoi premere `Super + Space` per aprire il Menu di Arch e da lì puoi fare praticamente tutto.

Ma il menu di Arch non è nemmeno pensato per essere il modo principale di usare il sistema la maggior parte del tempo. Possiamo fare più in fretta! Tutte le applicazioni più importanti sono assegnate direttamente a singoli tasti di scelta rapida. Avvii il terminale con `Super + Return` e un browser con `Super + Shift + Return`. Prova a farlo uno dopo l'altro e vedrai la magia del tiling di Hyprland in azione:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Puoi poi premere `Super + J` per impilarle una sopra l'altra invece che affiancate:

 ![navigation-stacked](images/navigation-stacked.webp)

Premi di nuovo `Super + J` per riportarle nelle loro posizioni affiancate. Poi prova `Super + Shift + Arrow Right` mentre sei sul browser per scambiare le finestre.



 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Ti sposti tra le finestre per scegliere quella che vuoi rendere attiva con `Super + Arrow`. Questo cambierà il focus e sposterà il cursore al centro della nuova applicazione.

Se premi `Super + Shift + 2`, sposterai l'applicazione attualmente attiva sul secondo workspace. `Super + Shift + 1` la riporta indietro. (E `Super + Shift + Alt + 2` sposterà l'applicazione attualmente attiva sul secondo workspace senza passare a esso).

Se tieni premuto `Super` e usi il mouse per fare clic su una finestra, potrai riorganizzare la sua posizione. Se tieni premuto `Super` e usi il pulsante destro del mouse, puoi ridimensionare liberamente la finestra.

Chiudi una finestra con `Super + W` o `Super + Q` (e chiudi tutte le finestre con `Ctrl + Alt + Delete`).

Puoi anche andare a schermo intero con `Super + F` o persino solo a tutta larghezza (mantenendo la barra superiore) con `Super + Alt + F` o a schermo intero all'interno di una finestra con `Super + Ctrl + F` (ottimo per YouTube!).

### Dwindle vs layout scorrevole

Il layout predefinito di Arch si chiama dwindle. Mantiene tutte le finestre che apri su un singolo workspace sempre visibili, anche se deve rimpicciolirle.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Ma puoi anche scegliere di trasformare un workspace nel layout scorrevole, in cui le finestre sono allineate una accanto all'altra, oltre il bordo visibile dello schermo. Trasformi un singolo workspace in questo layout tramite `Super + L`.


 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

La scelta è per workspace, e rimane. Così puoi tenere il workspace 1 su dwindle per navigare e il workspace 2 sullo scorrevole per il codice, e torneranno così dopo un riavvio.

Se desideri usare il layout scorrevole come predefinito, puoi impostarlo in `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Raggruppare le finestre

Le finestre possono essere raggruppate usando `Super + G`. Una volta che sei in un gruppo, ogni finestra che avvii mentre è attivo apparterrà al gruppo. Puoi spostarti tra queste finestre raggruppate usando `Super + Ctrl + Arrow Left/Right` o `Super + Alt + 1/2/3/4` per andare direttamente alla finestra raggruppata in ordine.

Puoi spostare una finestra fuori dal raggruppamento con `Super + Alt + G` o smontare l'intero gruppo premendo di nuovo `Super + G`. Infine, puoi spostare le finestre fuori dal gruppo al suo interno con `Super + Alt + Arrows`.

### Workspace scratchpad

Infine, c'è uno speciale workspace scratchpad che scende sopra qualsiasi workspace su cui ti trovi attualmente, proprio come una console di Quake. Attivalo e disattivalo con `Super + Grave` o `Super + S`, e posiziona lì una finestra usando `Super + Shift + Grave` o `Super + Alt + S`.

Funziona particolarmente bene per un terminale che esegue un agent, o per controlli con cui vuoi interagire rapidamente senza lasciare il workspace attuale. Per spostare una finestra fuori dallo scratchpad, inviala direttamente a un altro workspace con qualcosa come `Super + Shift + 1`.

Mentre lo scratchpad contiene una singola finestra, scende come un pannello centrato invece di estendersi su tutto lo schermo. Mettici una seconda app e torna a tutta larghezza, così le due hanno spazio per stare affiancate.

### Ci vuole un po' per abituarsi!

Ci vuole un po' di tempo per abituarsi a navigare sul desktop in questo modo, ma una volta che lo fai, sarà difficile tornare a un'esperienza desktop tradizionale guidata dal mouse!
