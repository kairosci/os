# Aktualizacje

Arch i twoje pakiety są utrzymywane na bieżąco za pośrednictwem _Aktualizuj > Arch_ w menu Arch (`Super + Space`).

Sam Arch jest instalowany jako zwykłe pakiety pacman z [Repozytorium Pakietów Arch](https://github.com/kairosci/os), więc aktualizacja instaluje [najnowszą wersję Arch](https://github.com/kairosci/os), uruchamia wszelkie oczekujące migracje, aby zsynchronizować system z najnowszą wersją, i aktualizuje wszystkie pakiety systemowe z [Mirror Arch Arch](https://github.com/kairosci/os) i [AUR](https://aur.archlinux.org/) (jeśli zainstalowałeś jakiekolwiek pakiety AUR).

Gdy zostaną wydane nowe wersje, po prawej stronie zegara pojawi się ikona strzałki w kółku. Kliknij ją, a rozpocznie się proces aktualizacji.

![update-available](images/update-available.webp)

### Cztery kanały

Arch jest aktualizowany wzdłuż czterech kanałów: stable, RC, edge i dev. Nowe instalacje rozpoczynają się na kanale stable, który śledzi [oficjalne wydania](https://github.com/kairosci/os), a także [stabilny mirror Arch Arch](https://github.com/kairosci/os), który działa miesiąc za najnowszym, abyśmy mogli wyłapać wszelkie nowe niekompatybilności wymagające zmian konfiguracji, zanim spowodują problemy dla ludzi.

Ale jeśli chcesz pomóc wyłapać te potencjalne problemy, możesz działać na kanale edge. To utrzyma twoje pakiety Arch śledzące najnowsze kompilacje deweloperskie i pozwoli ci aktualizować do najnowszych pakietów Arch, gdy tylko będą dostępne. Powinieneś robić to tylko, jeśli masz doświadczenie z Linuksem i wiesz, jak odzyskać system, który ma problemy.

Przed każdym nowym głównym wydaniem będziemy przeprowadzać finalną walidację przy użyciu kanału RC. Jeśli chcesz pomóc w finalnym dopracowaniu, wpadnij na #arch-release-candidates na Discordzie.

Na koniec jest kanał dev, który łączy Arch bezpośrednio z checkoutem git kodu źródłowego w `~/arch`, połączonym z pakietami edge. Powinieneś używać tego kanału tylko, jeśli jesteś doświadczonym użytkownikiem Linuksa, pracujesz bezpośrednio nad Arch i jesteś gotów tolerować awarie.

Możesz przełączać się między kanałami, używając _Aktualizuj > Channel_ z menu Arch (lub `arch-channel-set` w terminalu).

### Aktualizacje firmware

Twoje pakiety nie są jedyną rzeczą, która się starzeje. Wiele laptopów i urządzeń peryferyjnych dostarcza firmware BIOS, SSD i stacji dokującej poprzez Linux Vendor Firmware Service, a _Aktualizuj > Firmware_ w menu Arch pobierze i zainstaluje wszystko, co twój sprzęt ma w oczekiwaniu. Instaluje `fwupd` przy pierwszym uruchomieniu. Wiele firmware można zapisać tylko podczas ponownego uruchomienia, więc nie dziw się, jeśli zostaniesz o nie poproszony.

### Ostrzeżenie o bezpośrednich aktualizacjach pacman/yay

Jeśli znasz już Arch, możesz mieć pokusę, aby po prostu samodzielnie uruchomić `pacman -Syu` lub `yay -Syu`, ale jeśli to zrobisz, ominiesz snapshot, migracje i aktualizacje konfiguracji, które Arch uruchamia razem z nowymi pakietami. Dlatego Arch faktycznie zatrzyma bezpośrednią aktualizację systemu i wskaże ci zamiast tego `archctl update`. (Jeśli naprawdę wiesz, co robisz, strażnik powie ci, jak ominąć go dla pojedynczej transakcji).

### Wycofywanie złych aktualizacji

Jeśli kiedykolwiek będziesz mieć problem po wykonaniu aktualizacji, możesz wycofać system do snapshotu wykonanego przed aktualizacją. Po prostu uruchom ponownie i wybierz snapshot w menu ładowania bootowania sprzed rozpoczęcia aktualizacji.

![bootloader](images/bootloader.webp)

Jeśli w jakiś sposób twoje pliki konfiguracyjne zostały uszkodzone, możesz również wykonać reinstalację Arch, używając `arch reinstall` w terminalu. To zainstaluje ponownie wszystkie domyślne pakiety Arch, umieści cię na stable i obniży wersję wszelkich pakietów, które są zbyt nowe, oraz zresetuje wszystkie pliki konfiguracyjne. Zauważ, że wszystkie twoje zmiany konfiguracji użytkownika w domyślnych ustawieniach Arch zostaną nadpisane!
