# Avvisi

## Notifiche

Le notifiche mostrano informazioni rapide senza aprire un pannello. I codici di verifica possono essere copiati senza finire nella [cronologia degli appunti](08-unified-clipboard-history.md) e vengono cancellati dopo un minuto. Puoi aprire i link nel testo di una notifica con un clic.

La cronologia viene conservata per un giorno. Per cambiare durata, imposta `historyHours` nella sezione `notifications` di `~/.config/arch/shell.json`: `1` per un’ora, `168` per una settimana oppure `0` per non salvare la cronologia su disco.

## Avvisi da tastiera

Puoi consultare rapidamente data e ora, stato della batteria e meteo corrente con questi avvisi da scorciatoia.

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
