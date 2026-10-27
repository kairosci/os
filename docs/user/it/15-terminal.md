# Terminale

[Foot](https://codeberg.org/dnkl/foot) è il terminale predefinito di Arch. È veloce, leggero e compatibile anche con computer vecchi. Non supporta però schede o divisioni native.

Se usi Tmux, potrebbe non importarti, ma in caso contrario supportiamo completamente anche _Alacritty_, _Ghostty_ e _Kitty_ come opzioni. Scegli la tua preferenza sotto _Installa > Terminale_ nel menu Arch.

Avvii un nuovo terminale usando `Super + Return`. (Questa combinazione punterà automaticamente a qualsiasi Terminale tu abbia installato tramite _Installa > Terminale_, e puoi passare tra i terminali installati sotto _Impostazioni > Predefiniti > Terminale_.)

## Tmux

Tmux fornisce un'interfaccia coerente e programmabile per pannelli, finestre (dette anche schede) e sessioni riprendibili indipendentemente dal terminale. Funziona persino su host remoti, così quando sei in SSH su un server, puoi usare lo stesso approccio.

Avvii una nuova sessione Tmux in un terminale nuovo usando `Super + Alt + Return`, e poiché Tmux è un processo persistente, puoi riprendere la sessione anche se chiudi quel terminale. Premi semplicemente `Ctrl + Space` (chiamato tasto prefisso) poi `s` per vedere tutte le sessioni attive.

Arch viene fornito con una configurazione Tmux ottimizzata ergonomicamente, che ha molte combinazioni da imparare, quindi tieni [il foglio riassuntivo a portata di mano](07-hotkeys.md#tmux).
