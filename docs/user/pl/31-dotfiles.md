# Dotfiles

Arch jest konfigurowany głównie poprzez tzw. dotfiles, które żyją w `~/.config`. Są one uważane za twoje pliki do twoich zmian. Pliki, które żyją w `/usr/share/arch`, należą do samego Arch i nie powinieneś przy nich majstrować. Jeśli musisz zmienić cokolwiek w `/usr/share/arch`, powinieneś zamiast tego nadpisać wartość w `~/.config`.

Kluczowe konfiguracje można edytować bezpośrednio z menu Arch (`Super + Space`), takie jak _Ustawienia > Monitory_, _Ustawienia > Skróty_, _Ustawienia > Wejście_ i _Ustawienia > Config > [file]_. Gdy robisz to w ten sposób, każdy proces, który wymaga automatycznego ponownego uruchomienia po edycji konfiguracji, zrobi to po opuszczeniu edytora (domyślnie Neovim — `:wq`, pamiętaj! — ale możesz to zmienić w _Ustawienia > Defaults > Editor_).

Oto lista kluczowych plików w `~/.config` i tego, co kontrolują:

| File                  | Purpose              |
| ----------------------- | --------------------- |
| `~/.config/hypr/hyprland.lua` | Główna konfiguracja Hyprland. Ładuje domyślne ustawienia Arch oraz twoje pliki nadpisujące poniżej. [Dowiedz się więcej o konfiguracjach Hyprland](https://wiki.hypr.land/Configuring/).  |
| `~/.config/hypr/bindings.lua` | Twoje własne skróty klawiszowe i nadpisania domyślnych. |
| `~/.config/hypr/monitors.lua` | Kontroluje twoje monitory, rozdzielczość i pozycję. |
| `~/.config/hypr/input.lua` | Kontroluje układ klawiatury, mysz i ustawienia gładzika. |
| `~/.config/hypr/looknfeel.lua` | Kontroluje odstępy, obramowania, animacje i resztę wyglądu. |
| `~/.config/hypr/autostart.lua` | Kontroluje dodatkowe procesy uruchamiane z sesją. |
| `~/.config/arch/shell.json` | Kontroluje powłokę Arch: pozycję paska, układ i widżety, plus czasy wygaszacza, blokady i bezczynności. |
| `~/.config/foot/foot.ini` | Kontroluje twój terminal (foot jest domyślny). |
| `~/.XCompose` | Definiuje twoje emoji szybkiego dostępu i autouzupełnianie imienia/e-maila. Upewnij się, że uruchomisz `arch-restart-xcompose` po wprowadzeniu zmian. |

Jeśli skończysz wprowadzać wiele zmian, aby dostosować własną konfigurację, dobrym pomysłem jest wykonanie kopii zapasowej wszystkich tych dotfiles. [Stow jest świetnym sposobem, aby to zrobić](https://www.youtube.com/watch?v=NoFiYOqnC4o).

### Uruchamianie własnych aplikacji z sesją

Jeśli chcesz, aby coś działało przy każdym logowaniu — demon synchronizacji, aplikacja czatu, twój własny skrypt — umieść to w `~/.config/hypr/autostart.lua`:

```lua
o.launch_on_start("my-service")
```

To uruchamia polecenie jako część sesji, więc jest prawidłowo sprzątane, gdy wylogujesz się ponownie.

### Uruchamianie skryptów przy zdarzeniach systemowych

Arch uruchamia hooki w kilku momentach i możesz zawiesić na nich własne skrypty. Żyją one w `~/.config/arch/hooks/<event>.d/`, jeden katalog na zdarzenie, a każdy plik wykonywalny tam uruchamia się, gdy zdarzenie nastąpi:

| Event | When it runs |
| ----- | ------------ |
| `post-boot` | Zaraz po uruchomieniu pulpitu |
| `post-update` | Pod koniec `archctl update`, po pakietach, migracjach i restartach usług, przed aktualizacją narzędzi mise |
| `pre-refresh-pacman` | Po tym, jak `archctl refresh pacman` ponownie synchronizuje konfigurację pakietów, przed aktualizacją pakietów; przełączenie kanału uruchamia to podczas tego samego kroku odświeżania |
| `theme-set` | Po zmianie motywu (nazwa motywu w `$1`) |
| `font-set` | Po zmianie czcionki (nazwa czcionki w `$1`) |
| `battery-low` | Gdy poziom baterii jest niski (procent w `$1`) |

Hook `pre-refresh-pacman` to miejsce, w którym należą niestandardowe repozytoria lub wiersze `IgnorePkg`, ponieważ uruchamia się przed transakcją pakietów. Oba hooki związane z aktualizacją działają jako twój użytkownik po tym, jak Arch czyści swoją pamięć podręczną autoryzację sudo, więc hook używający `sudo` potrzebuje własnej autoryzacji i może poprosić o twoje hasło.

Każdy z tych katalogów zawiera już plik `.sample` pokazujący kształt hooka — upuść `.sample` z nazwy, aby wdrożyć go do pracy. Aby zainstalować skrypt napisany w innym miejscu, użyj `archctl hook install post-boot ~/my-hook`, co kopiuje go i czyni wykonywalnym.

### Dodawanie własnych wpisów menu

Menu Arch (`Super + Space`) można rozszerzyć o własne wiersze, edytując `~/.config/arch/extensions/arch-menu.jsonc`. Wpisy są kluczowane kropkowym id, a id jest tym, co umieszcza je w drzewie, więc `personal` pojawia się w menu głównym, a `personal.notes` pojawia się wewnątrz niego:

```jsonc
"personal": {"icon":"","label":"Personal"},
"personal.notes": {"icon":"󰎞","label":"Notes","action":"arch-launch-editor ~/notes"},
```

Użyj ponownie istniejącego id, a nadpiszesz ten wiersz zamiast dodawać nowy. Plik jest dostarczany ze wszystkimi dostępnymi polami udokumentowanymi jako komentarze.

### Dodawanie własnych eksportów powłoki, funkcji i aliasów

Arch dostarcza zestaw ergonomicznych aliasów i pomocnych funkcji, ale bardzo często chce się dodać własne. Powinieneś dodawać zarówno aliasy, funkcje, jak i eksporty w `~/.bashrc`. Ten plik nie zostanie nadpisany podczas aktualizacji. Jeśli chcesz zmienić którekolwiek z domyślnych ustawień Arch, możesz również bezpiecznie dodać je tutaj.

### Zmienianie wewnętrznych plików Arch

Słuchaj, to jest twój komputer. Możesz z nim robić, co chcesz, ale odradzałbym wprowadzanie zmian bezpośrednio w plikach w `/usr/share/arch`. Należą do pakietu pacman Arch, więc twoje zmiany zostaną po prostu nadpisane przy następnej aktualizacji. Lepiej zamiast tego nadpisać wszelkie domyślne wartości, których nie lubisz, w folderze `~/.config/*`.

Możesz zmienić w ten sposób prawie wszystko, w tym domyślne skróty klawiszowe. Po prostu edytuj `~/.config/hypr/bindings.lua`, aby powiedzmy zastąpić [Obsidian](https://obsidian.md/) przez [Joplin](https://joplinapp.org/) (zainstaluj za pomocą `arch-pkg-add joplin-bin`):

```lua
o.rebind("SUPER + SHIFT + O", "Joplin", "joplin-desktop")
```

`o.rebind` usuwa istniejące powiązanie przed dodaniem jego zamiennika. Przyjmuje te same argumenty co `o.bind`, w tym pomocniki uruchamiania i opcje powiązań. Użyj `o.bind`, aby dodać powiązanie, lub `hl.unbind`, aby usunąć je bez zastępowania.

Jeśli nalegasz na hackowanie wewnętrznych plików Arch, przełącz się na kanał dev za pośrednictwem _Aktualizuj > Channel > Dev_. To łączy Arch z checkoutem git kodu źródłowego w `~/arch`, który możesz swobodnie zmieniać do woli. Nikt tu nie będzie ci mówił, co robić!

### Resetowanie wszelkich zmian

Jeśli skończysz robiąc bałagan w konfiguracjach, zawsze możesz przywrócić je do domyślnych za pośrednictwem _Aktualizuj > Config_ w menu Arch. Lub uruchamiając `arch reinstall configs`, aby zresetować wszystko.
