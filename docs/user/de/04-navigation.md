# Navigation

Alles in Arch läuft über die Tastatur — _ALLES!_ Wenn das System zum ersten Mal startet, kannst du buchstäblich nichts allein mit der Maus tun. Aber du kannst `Super + Space` drücken, um das Arch-Menü einzublenden, und von hier aus kannst du so ziemlich alles tun.

Aber das Arch-Menü ist nicht einmal als der Hauptweg gedacht, das System die meiste Zeit zu bedienen. Wir können schneller als das sein! Alle wichtigsten Anwendungen sind direkt an einzelne Hotkeys gebunden. Das Terminal startest du mit `Super + Return` und einen Browser mit `Super + Shift + Return`. Probiere beides nacheinander aus, und du siehst die Magie von Hyprlands Tiling in Aktion:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Du kannst dann `Super + J` drücken, um sie übereinander statt nebeneinander zu stapeln:

 ![navigation-stacked](images/navigation-stacked.webp)

Drücke erneut `Super + J`, um sie in ihre Positionen nebeneinander zurückzubringen. Probiere dann `Super + Shift + Arrow Right` aus, während du auf dem Browser bist, um die Fenster zu tauschen.



 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Zwischen den Fenstern, die aktiv sein sollen, navigierst du mit `Super + Arrow`. Das wechselt den Fokus und bewegt den Cursor in die Mitte der neuen Anwendung.

Wenn du `Super + Shift + 2` drückst, verschiebst du die aktuell fokussierte Anwendung auf den zweiten Arbeitsbereich. `Super + Shift + 1` verschiebt sie zurück. (Und `Super + Shift + Alt + 2` verschiebt die aktuell fokussierte Anwendung auf den zweiten Arbeitsbereich, ohne zu ihm zu wechseln).

Wenn du `Super` gedrückt hältst und mit der Maus auf ein Fenster klickst, kannst du neu anordnen, wo es sitzt. Wenn du `Super` gedrückt hältst und die rechte Maustaste benutzt, kannst du das Fenster frei in der Größe verändern.

Du schließt ein Fenster mit `Super + W` oder `Super + Q` (und schließt alle Fenster mit `Ctrl + Alt + Delete`).

Du kannst auch mit `Super + F` in den Vollbildmodus gehen oder auch nur mit `Super + Alt + F` auf volle Breite (wobei die obere Leiste bleibt) oder mit `Super + Ctrl + F` in den Vollbildmodus innerhalb eines Fensters (gut für YouTube!).

### Dwindle- vs. Scrolling-Layout

Archs Standardlayout heißt dwindle. Es hält alle Fenster, die du auf einem einzelnen Arbeitsbereich öffnest, jederzeit sichtbar, selbst wenn es sie dafür verkleinern muss.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Aber du kannst einen Arbeitsbereich auch in das Scrolling-Layout versetzen, bei dem die Fenster nebeneinander aufgereiht sind, über den sichtbaren Rand des Displays hinaus. Einen einzelnen Arbeitsbereich versetzt du mit `Super + L` in dieses Layout.


 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Die Wahl gilt pro Arbeitsbereich, und sie bleibt bestehen. So kannst du Arbeitsbereich 1 auf dwindle zum Surfen und Arbeitsbereich 2 auf Scrolling für Code lassen, und sie kommen nach einem Neustart so zurück.

Wenn du das Scrolling-Layout als Standard verwenden möchtest, kannst du das in `~/.config/hypr/looknfeel.lua` einstellen:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Fenster gruppieren

Fenster können mit `Super + G` gruppiert werden. Sobald du in einer Gruppe bist, gehört jedes Fenster, das du startest, solange das aktiv ist, zu dieser Gruppe. Zwischen diesen gruppierten Fenstern kannst du dich mit `Super + Ctrl + Arrow Left/Right` bewegen oder mit `Super + Alt + 1/2/3/4` direkt zu einem gruppierten Fenster in der Reihenfolge wechseln.

Du kannst ein Fenster mit `Super + Alt + G` aus der Gruppierung herausbewegen oder die gesamte Gruppe auflösen, indem du erneut `Super + G` drückst. Schließlich kannst du Fenster außerhalb der Gruppe mit `Super + Alt + Arrows` in sie hineinbewegen.

### Scratchpad-Arbeitsbereich

Schließlich gibt es einen speziellen Scratchpad-Arbeitsbereich, der über den Arbeitsbereich herunterklappt, auf dem du dich gerade befindest, ganz wie eine Quake-Konsole. Schalte ihn mit `Super + Grave` oder `Super + S` um und platziere ein Fenster dort mit `Super + Shift + Grave` oder `Super + Alt + S`.

Er eignet sich besonders gut für ein Terminal, in dem ein Agent läuft, oder für Steuerelemente, mit denen du schnell interagieren möchtest, ohne den aktuellen Arbeitsbereich zu verlassen. Um ein Fenster vom Scratchpad wegzubewegen, sende es direkt an einen anderen Arbeitsbereich mit etwa `Super + Shift + 1`.

Solange der Scratchpad ein einzelnes Fenster enthält, klappt er als zentrales Panel herunter, anstatt den Bildschirm zu überspannen. Platziere eine zweite App darauf und er kehrt zur vollen Breite zurück, damit die beiden Platz haben, nebeneinander zu sitzen.

### Es braucht etwas Gewöhnung!

Es braucht ein wenig Zeit, sich daran zu gewöhnen, auf dem Desktop so zu navigieren, aber sobald du es tust, wird es schwer sein, zu einer traditionellen, mausgesteuerten Desktop-Erfahrung zurückzukehren!
