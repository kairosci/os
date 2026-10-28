# Sicurezza

Arch prende la sicurezza estremamente sul serio. Deve essere un sistema operativo che puoi usare per fare _Lavoro Vero_ nel _Mondo Reale_. Dove perdere un portatile non può portare a un'emergenza di sicurezza. Ecco quindi cosa facciamo:

1. *La crittografia completa del disco è obbligatoria*: questo è il passaggio più importante per proteggere fisicamente i tuoi dati. Se il computer viene perso o rubato, i dati sono completamente crittografati usando il LUKS standard (Linux Unified Key Setup).
2. *Il firewall è attivo per impostazione predefinita*: tutto il traffico in entrata è bloccato per impostazione predefinita, tranne la porta 53317 per [LocalSend](https://localsend.org/). Persino ssh è disattivato finché non lo attivi tramite _Impostazioni > Sicurezza > SSHD_, che apre la porta 22 (con limitazione della frequenza contro gli attacchi brute force) come parte della configurazione. Blindiamo persino l'accesso a Docker usando la configurazione [ufw-docker](https://github.com/chaifeng/ufw-docker) per impedire che i tuoi container vengano accidentalmente esposti al mondo.
3. *Arch ha sempre gli ultimi aggiornamenti*: Arch, la distribuzione sottostante su cui è costruito Arch, è una distribuzione rolling. Questo significa che qualsiasi vulnerabilità di sicurezza scoperta e corretta in qualsiasi pacchetto diventa rapidamente disponibile per l'installazione usando `arch-update`. In questo modo esegui sempre le versioni più recenti e sicure di tutto.
4. *Arch mantiene pacchetti e mirror propri*: per impostazione predefinita, Arch si affida solo ai pacchetti dei repository core/extra/multilib di Arch e al proprio Arch Package Repository. Puoi installare software direttamente da AUR, ma l'installazione di base non lo fa: solo alcune installazioni opzionali, come i browser di terze parti, attingono da AUR.
5. *Cloudflare ci protegge dai DDoS*: tutta l'infrastruttura di distribuzione di Arch — le ISO, i pacchetti Arch, il mirror Arch — è protetta dietro il formidabile scudo anti-DDoS di Cloudflare e ospitata sulla sua CDN. Questo garantisce una disponibilità eccellente.

## Cambiare le password

Su un'installazione crittografata hai due password: quella che sblocca il disco all'avvio e quella con cui accedi e usi `sudo`. La configurazione iniziale le rende uguali. Entrambe possono essere cambiate in _Aggiorna > Password_ nel menu di Arch: _Crittografia disco_ per la prima, _Utente_ per la seconda. Cambiare la password del disco chiede prima quella attuale, quindi tienila a portata di mano. Se un cambiamento viene interrotto, apri di nuovo _Crittografia disco_: chiederà la password che sblocca il disco adesso e completerà il cambiamento.

## Passare a qualcun altro una macchina già usata

Se stai consegnando la tua macchina a qualcun altro, non devi reinstallarla. Apri _Impostazioni > Reimposta computer_ nel menu di Arch, digita `reset` per confermare e riavvia. Questo cancella ogni account utente e tutto ciò che è in `/home`, butta via tutti i pacchetti e le modifiche di sistema che hai fatto dall'installazione e cancella l'identità della macchina: connessioni di rete, chiavi host e tutto il resto. Ciò che si riavvia è la procedura guidata di configurazione del primo avvio, pronta perché il nuovo proprietario inserisca il proprio nome, la propria password e la propria password di crittografia.

Funziona ripristinando lo snapshot di base che il programma di installazione crea, quindi è disponibile solo sulle macchine installate dall'ISO di Arch. E su un disco senza crittografia, una reimpostazione è una cancellazione piuttosto che una cancellazione sicura, quindi se i dati erano sensibili, fai invece un'installazione pulita.

## Chiavi di firma

La chiave pubblica per tutte le firme ISO e i pacchetti del repository Arch è `40DFB630FF42BCFFB047046CF0134EE680CAC571` ([verifica su openpgp.org](https://keys.openpgp.org/search?q=pkgs%40github.com/kairosci/os)). Anche il pacchetto `arch/arch-keyring` la contiene e verrà usato per distribuire senza intoppi eventuali aggiornamenti.

Puoi trovare la firma per qualsiasi rilascio ISO aggiungendo .sig all'URL. Come https://iso.github.com/kairosci/os/arch-x.x.x.iso.sig.
