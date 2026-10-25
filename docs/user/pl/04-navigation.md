# Nawigacja

Wszystko w Arch dzieje się przez klawiaturę — _WSZYSTKO!_ Gdy system uruchamia się po raz pierwszy, dosłownie nic nie zrobisz samą myszą. Ale możesz nacisnąć `Super + Space`, aby wyświetlić menu Arch, a stamtąd zrobisz niemal wszystko.

Ale menu Arch nie ma nawet być przez większość czasu głównym sposobem obsługi systemu. Możemy działać szybciej! Wszystkie najważniejsze aplikacje są przypisane bezpośrednio do poszczególnych skrótów klawiszowych. Terminal uruchamiasz za pomocą `Super + Return`, a przeglądarkę za pomocą `Super + Shift + Return`. Spróbuj zrobić jedno po drugim, a zobaczysz magię kafelkowania Hyprland w akcji:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Następnie możesz nacisnąć `Super + J`, aby ułożyć je jedno nad drugim zamiast obok siebie:

 ![navigation-stacked](images/navigation-stacked.webp)

Naciśnij `Super + J` ponownie, aby przywrócić je do pozycji obok siebie. Następnie spróbuj `Super + Shift + Arrow Right` w przeglądarce, aby zamienić okna miejscami.



 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Pomiędzy oknami, które mają być aktywne, poruszasz się za pomocą `Super + Arrow`. Spowoduje to przełączenie fokusu i przeniesienie kursora na środek nowej aplikacji.

Jeśli naciśniesz `Super + Shift + 2`, przeniesiesz bieżącą aplikację z fokusem na drugi obszar roboczy. `Super + Shift + 1` przenosi ją z powrotem. (A `Super + Shift + Alt + 2` przeniesie bieżącą aplikację z fokusem na drugi obszar roboczy bez przełączania się na niego).

Jeśli przytrzymasz `Super` i klikniesz okno myszą, będziesz mógł zmienić jego położenie. Jeśli przytrzymasz `Super` i użyjesz prawego przycisku myszy, możesz swobodnie zmieniać rozmiar okna.

Okno zamykasz za pomocą `Super + W` lub `Super + Q` (a wszystkie okna zamykasz za pomocą `Ctrl + Alt + Delete`).

Możesz też przejść na pełny ekran za pomocą `Super + F`, a nawet tylko na pełną szerokość (zachowując górny pasek) za pomocą `Super + Alt + F` lub na pełny ekran wewnątrz okna za pomocą `Super + Ctrl + F` (dobre na YouTube!).

### Dwindle kontra układ scrolling

Domyślny układ Arch nazywa się dwindle. Utrzymuje wszystkie okna otwarte na jednym obszarze roboczym widoczne przez cały czas, nawet jeśli musi je zmniejszyć.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Ale możesz też wybrać, aby zamienić obszar roboczy w układ scrolling, w którym okna są ustawione obok siebie, poza widoczną krawędź ekranu. Pojedynczy obszar roboczy zamieniasz w ten układ za pomocą `Super + L`.


 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Wybór dotyczy każdego obszaru roboczego osobno i zostaje zapamiętany. Możesz więc zostawić obszar roboczy 1 na dwindle do przeglądania, a obszar roboczy 2 na scrolling do kodu, a po restarcie wrócą w ten sposób.

Jeśli chcesz używać układu scrolling jako domyślnego, możesz to ustawić w `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Grupowanie okien

Okna można grupować za pomocą `Super + G`. Gdy już znajdziesz się w grupie, każde okno, które uruchomisz, gdy jest ona aktywna, będzie należało do tej grupy. Możesz poruszać się między tymi pogrupowanymi oknami za pomocą `Super + Ctrl + Arrow Left/Right` lub `Super + Alt + 1/2/3/4`, aby przejść bezpośrednio do pogrupowanego okna w kolejności.

Możesz przenieść okno poza grupowanie za pomocą `Super + Alt + G` lub rozłożyć całą grupę, naciskając ponownie `Super + G`. Na koniec możesz przenieść okna spoza grupy do niej za pomocą `Super + Alt + Arrows`.

### Obszar roboczy scratchpad

Na koniec jest specjalny obszar roboczy scratchpad, który opada na obszar roboczy, na którym właśnie jesteś, podobnie jak konsola w Quake. Przełączaj go za pomocą `Super + Grave` lub `Super + S`, a okno umieszczaj tam za pomocą `Super + Shift + Grave` lub `Super + Alt + S`.

Działa szczególnie dobrze dla terminala z uruchomionym agentem lub dla elementów sterujących, z którymi chcesz szybko interagować bez opuszczania bieżącego obszaru roboczego. Aby przenieść okno ze scratchpada, wyślij je bezpośrednio na inny obszar roboczy czymś w rodzaju `Super + Shift + 1`.

Gdy scratchpad zawiera jedno okno, opada jako wyśrodkowany panel, zamiast rozciągać się na cały ekran. Umieść na nim drugą aplikację, a wróci do pełnej szerokości, dzięki czemu obie będą miały miejsce, aby usiąść obok siebie.

### Trzeba się do tego trochę przyzwyczaić!

Przyzwyczajenie się do nawigowania po pulpicie w ten sposób zajmuje chwilę, ale gdy już to zrobisz, trudno będzie wrócić do tradycyjnego pulpitu napędzanego myszą!
