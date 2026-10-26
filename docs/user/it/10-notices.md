# Avvisi

## Notifiche

Le notifiche compaiono nell'angolo in alto a destra dello schermo attivo. Quelle provenienti dalla stessa app o sito si raccolgono in un mazzo, così un canale Slack molto attivo non nasconde un errore di compilazione. Passa il puntatore sul mazzo per aprirlo; mentre leggi non arrivano nuove notifiche sotto il puntatore. Fai clic su una scheda per aprire l'origine, oppure fai clic con il tasto centrale o sulla ✕ per chiuderla.

Le schede mostrano le azioni disponibili: _Copia codice_ per i codici di verifica (che restano fuori dalla [cronologia unificata degli appunti](08-unified-clipboard-history.md) e vengono cancellati dopo un minuto), oltre ai pulsanti forniti dall'app. I collegamenti nel testo di una notifica si aprono al clic.

Passa il puntatore su una scheda e fai clic su zzz accanto alla chiusura, oppure fai clic destro sulla scheda, per sospendere le notifiche di quell'origine per 15 minuti, un'ora o fino alla mattina seguente. Le notifiche sospese vengono trattenute, non eliminate.

Fai clic destro sulla campana della barra (passa il puntatore al centro della barra per mostrarla) per aprire il pannello notifiche: elementi trattenuti, notifiche recenti e cronologia dell'ultimo giorno. Da lì puoi sospendere tutto, riattivare un'origine o scegliere se ricevere i codici di verifica mentre non vuoi essere disturbato (per impostazione predefinita sì). L'ingranaggio apre le preferenze per lo schermo da usare, la sospensione durante i giochi a schermo intero e la sospensione durante la condivisione dello schermo. Quando condividi lo schermo, la campana offre una sospensione temporanea; l'audio non viene silenziato finché non ne scegli una.

La cronologia viene conservata per un giorno. Per cambiarlo, imposta `historyHours` nella sezione `notifications` di `~/.config/arch/shell.json` su `1`, `168` per una settimana oppure `0` per non conservarla su disco, per esempio `"notifications": { "historyHours": 168 }`.

## Avvisi da scorciatoia

Puoi accedere rapidamente a data e ora, stato batteria e meteo corrente usando gli avvisi da scorciatoia.

### Data e ora

`Super + Ctrl + Alt + T`

 ![notice-datetime](images/notice-datetime.webp)

### Meteo

`Super + Ctrl + Alt + W`

 ![notice-weather](images/notice-weather.webp)

La posizione viene rilevata dal tuo indirizzo IP, che di solito è abbastanza vicina, ma non sempre. Puoi fissarla con `arch weather location --set Malibu`, oppure essere preciso aggiungendo le coordinate: `arch weather location --set Malibu 34.0259,-118.7798`. Esegui `arch weather location` da solo per vedere dove pensa che tu sia, e `--clear` per tornare al rilevamento automatico.

### Batteria

`Super + Ctrl + Alt + B`

 ![notice-battery](images/notice-battery.webp)
