# GUI

## Files

Files (Nautilus) è il file manager grafico. `Super + Shift + F` lo apre, e `Super + Shift + Alt + F` lo apre nella directory in cui si trova il tuo terminale, il che fa risparmiare molti clic. `Ctrl + L` ti permette di digitare un percorso, e premere `Space` su qualsiasi file ti dà un'anteprima rapida senza aprire nulla.

Collega una chiavetta USB o una scheda SD e verrà montata automaticamente, così apparirà semplicemente nella barra laterale. Per qualcosa di più complesso — formattare un'unità, controllare lo stato SMART, creare partizioni — avvia _Disks_ dal launcher delle app (`Super + Space`).

Il doppio clic segue impostazioni predefinite sensate: le immagini si aprono in imv, i video in mpv, i PDF in Document Viewer e il testo semplice in Neovim.

## Disktree

Quando l'unità si riempie e non hai idea di cosa la stia mangiando, avvia [Disktree](https://github.com/tobi/disktree) dal launcher delle app (`Super + Space`). Mostra una treemap grafica della tua directory home. I blocchi più grandi occupano più spazio; esplora le directory con tastiera o mouse, segna ciò che deve andare e rivedi le tue selezioni prima di rimuovere qualsiasi cosa. Esegui `disktree --disk` per scansionare l'intero disco.

## Obsidian

[Obsidian](https://obsidian.md/) è un'applicazione per prendere appunti gratuita e altamente estensibile che usa semplici file Markdown per l'archiviazione.

Obsidian è gratuito per tutti gli scopi, incluso l'uso personale, commerciale e senza scopo di lucro.

Obsidian offre anche un [componente aggiuntivo commerciale per la sincronizzazione](https://obsidian.md/sync) con app mobili su iOS e Android. (https://obsidian.md/pricing).

Avvii Obsidian con `Super + Shift + O`. Per usare la sincronizzazione del tema, devi selezionare il tema `Arch` nelle impostazioni.

## Pinta

[Pinta](https://www.pinta-project.com/) è uno strumento di modifica delle immagini di base, ottimo per ritagliare, ridimensionare e altre manipolazioni di base. Non aspettarti però un'alternativa a Photoshop. Ma ha comunque la Bacchetta magica e i livelli!

Avvii Pinta dal launcher delle app (`Super + Space`).

## Aether

[Aether](https://github.com/bjarneo/aether) è un'applicazione per i temi che può estrarre colori da un'immagine di sfondo e trasformarli in un tema completo e coerente. È il modo più semplice per [creare il tuo tema](43-making-your-own-theme.md).

Avvii Aether dal launcher delle app (`Super + Space`).

## LocalSend

[LocalSend](https://localsend.org/) ti permette di inviare file ad altri dispositivi sulla stessa rete che eseguono l'app, come AirDrop di Apple. È però multipiattaforma, quindi puoi inviare file da e verso Windows, macOS, Android, iOS e naturalmente Linux.

Puoi aprire il menu Condividi con `Super + Ctrl + S` oppure in _Azioni > Condividi_ nel menu Arch. Ti offre quattro opzioni:

- **Appunti** invia ciò che hai copiato come file di testo. Ottimo per portare un link o uno snippet sul telefono senza inviarti un'email.
- **File** apre un selettore di file in cui puoi selezionarne diversi contemporaneamente.
- **Cartella** invia un'intera directory.
- **Ricevi** apre LocalSend vero e proprio così un altro dispositivo può inviarti qualcosa.

La stessa cosa funziona dal terminale con `arch share clipboard`, `arch share file [path]` e `arch share folder [path]`. Ometti il percorso e otterrai il selettore.

Puoi anche inviare direttamente dal file manager: fai clic con il tasto destro su qualsiasi selezione in Nautilus e scegli _Send via LocalSend_.

Il firewall di Arch è chiuso per impostazione predefinita tranne che per la porta di LocalSend, quindi funziona subito su un'installazione nuova. Vedi [sicurezza](48-security.md).

## LibreOffice

[LibreOffice](https://www.libreoffice.org/) è una suite per ufficio completa con elaboratore di testi, foglio di calcolo, presentazioni, applicazione di disegno e altro. È compatibile con i file di Microsoft Office, quindi è un ottimo modo per poter aprire quei documenti Word.

Avvii LibreOffice dal launcher delle app (`Super + Space`).

## Signal

[Signal](https://signal.org/) è il pioniere della messaggistica con crittografia end-to-end, e un'ottima opzione di comunicazione per chi preferisce non passare da uno dei grandi conglomerati tecnologici.

Avvii Signal con `Super + Shift + G`. Non fa parte dell'installazione di base, quindi la prima volta che premi quella combinazione Arch ti offrirà di installarlo per te (si trova anche in _Installa > Servizio_ nel menu Arch).

## mpv

[mpv](https://mpv.io/) è un lettore multimediale semplice e veloce che riproduce quasi tutto da qualsiasi sorgente. Ottimo per guardare video.

Avvii mpv dal launcher delle app (`Super + Space`) oppure fai semplicemente doppio clic su un video nel file manager.
