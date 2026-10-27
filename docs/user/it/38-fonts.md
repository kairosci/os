# Caratteri

Per impostazione predefinita, Arch usa JetBrainsMono Nerd Font sia come carattere del terminale sia come carattere di sistema.

 ![fonts-jetbrainsmono](images/fonts-jetbrainsmono.webp)

Puoi cambiarlo dal menu _Stile > Carattere_ nel menu di Arch (`Super + Space`). Questo imposta il carattere a spaziatura fissa ovunque: nel terminale, nella barra e in qualsiasi altra cosa lo richieda.

Puoi installare altri popolari caratteri per programmare tramite _Installa > Stile > Carattere_ nel menu di Arch: Cascadia Mono, Meslo LG Mono, Fira Code, Victor Code, Bitstream Vera Mono e Iosevka sono tutti a un clic di distanza, nelle loro versioni Nerd Font, così i glifi nella barra e nel terminale continuano a funzionare. Dopo averne installato uno, sceglilo in _Stile > Carattere_.

## Cinese, giapponese e coreano

Cinese, giapponese e coreano condividono molti caratteri, ma alcuni vengono disegnati in modo diverso: lo stesso carattere può apparire corretto a un lettore e straniero a un altro. Scegliendo una di queste lingue in _Setup > Lingua_, o il relativo metodo di input, vengono usate le forme corrispondenti. Per sceglierle manualmente, esegui `archctl font cjk jp`, `kr`, `sc`, `tc` (Taiwan) o `hk` (Hong Kong) nel terminale; `archctl font cjk default` ripristina la scelta del sistema, che usa le forme giapponesi. Il testo di una pagina web o di un documento contrassegnato con la propria lingua, e l'intero desktop mentre usa una di queste lingue, mantiene le forme corrispondenti.
