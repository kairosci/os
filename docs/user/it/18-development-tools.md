# Strumenti di sviluppo

## Editor alternativi

Arch include [Neovim](https://neovim.io/) come editor predefinito, ma se vuoi qualcosa di più comune e familiare puoi aprire il menu Arch (`Super + Space`) e vedere le opzioni in _Installa > Editor_. Troverai VSCode, Cursor, Zed, Sublime Text, Helix, Vim ed Emacs. Se non trovi quello che cerchi, dai un'occhiata a _Installa > Pacchetto_ per vedere se esiste un pacchetto Arch (e in caso contrario prova _Installa > AUR_ per controllare l'AUR).

Anche l'editor `vi` originale è disponibile subito. Esegui `vi filename` per modificare un file nel terminale.

L'abbinamento del tema è disponibile per `VSCode`, `Cursor`, `VSCodium` e `Helix`.

Puoi impostare l'editor predefinito a livello di sistema in `Setup > Defaults > Editor`.

## Ambienti

Arch consente di configurare moltissimi ambienti di sviluppo dalla sezione _Installa > Sviluppo_ del menu Arch (`Super + Space`). Troverai naturalmente _Ruby on Rails_, ma anche tutti e tre i principali runtime JavaScript (Node.js, Bun, Deno) e popolari framework PHP come Laravel e Symfony. Ah, e ci sono anche Go, Rust, Python, Java, Elixir (con Phoenix), .NET, OCaml, Zig, Clojure e Scala. È una selezione davvero ampia!

La maggior parte di questi ambienti è gestita da [Mise](https://mise.jdx.dev/). È uno strumento che ti permette di installare ed eseguire più versioni di un linguaggio di programmazione sulla stessa macchina. È come rbenv o rvm per Ruby o virtualenv per Python, ma funziona per molti ambienti diversi.

Per installare, ad esempio, Ruby, esegui `mise use -g ruby`: installerà Ruby e lo imposterà come predefinito globale. Oppure, se il tuo progetto ha un file .ruby-version, puoi semplicemente eseguire `mise i` nella radice del progetto.

## Strumenti CLI preinstallati

Arch rende disponibili strumenti come `gh` e `uv` tramite [l'installazione differita di mise](https://mise.jdx.dev/dev-tools/shims.html#lazy-tools). Al primo avvio, mise installa lo strumento. Gli avvii successivi riutilizzano la versione installata, senza controllare gli aggiornamenti a ogni esecuzione.

Puoi consultare le impostazioni predefinite o installare gli strumenti in anticipo:

```bash
mise ls --current              # List the tools configured for this directory
mise install gh               # Install one tool now
mise install --include-lazy    # Install all configured tools, including lazy tools
```

Esegui `archctl update` per aggiornare gli strumenti installati insieme al resto di Arch. L'alias `mup` aggiorna soltanto gli strumenti gestiti da mise. Per aggiungere un altro strumento alla tua configurazione, usa `mise use -g <tool>`.

La configurazione Python installa anche `uv` tramite mise. Rimuovendo l'ambiente di sviluppo Python, `uv` resta disponibile come strumento indipendente.

## Docker

[Docker](https://www.docker.com/) non ha certo bisogno di presentazioni. Ti permette di eseguire container isolati e Arch installa tutto il necessario per farlo funzionare bene, incluso Docker stesso e [Docker Compose](https://docs.docker.com/compose/).

Per impostazione predefinita il tuo utente *non* appartiene al gruppo `docker`. Quel gruppo equivale di fatto a root: un container può montare `/` e prendere il controllo della macchina. Usa Docker con `sudo` (`sudo docker ps`, `sudo docker compose up`); gli strumenti grafici che ne hanno bisogno chiedono l’autorizzazione. Se il tuo account appartiene già al gruppo `docker`, rimuovilo con `sudo gpasswd -d "$USER" docker` e avvia una nuova sessione perché la modifica abbia effetto.

Puoi configurare i database più comuni per lo sviluppo locale in Docker da _Installa > Sviluppo > Docker DB_ nel menu Arch.

## GitHub CLI

[La GitHub CLI](https://cli.github.com/) ti permette di autenticarti con il tuo account GitHub e clonare repository privati usandola. È collegata come uno degli stub mise a caricamento differito, quindi la prima volta che esegui `gh` si installa da sola. Per autenticarti, esegui `gh auth login`. Poi puoi clonare repository privati con `gh repo clone org/repo`.

Con questo comando puoi eseguire anche molte altre operazioni su GitHub. Esegui semplicemente `gh` per vedere tutto ciò che è possibile.

C'è anche uno stub a installazione differita per `ghui` per gestire le tue pull request in una TUI. E [lazygit](https://github.com/jesseduffield/lazygit) è preinstallato, se vuoi gestire git stesso da una TUI.
