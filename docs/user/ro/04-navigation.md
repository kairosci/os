# Navigare

Totul în Arch se face de la tastatură — _TOTUL!_ Când pornește sistemul prima dată, literalmente nu poți face nimic doar cu mouse-ul. Dar poți apăsa `Super + Space` pentru a deschide Meniul Arch și, de aici, poți face cam tot.

Dar meniul Arch nici măcar nu este gândit să fie modul principal de operare a sistemului în majoritatea timpului. Putem fi mai rapizi de atât! Toate aplicațiile cele mai importante sunt legate direct de taste rapide individuale. Pornești terminalul cu `Super + Return` și un browser cu `Super + Shift + Return`. Încearcă să le faci una după alta și vei vedea magia dispunerii în mozaic din Hyprland în acțiune:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Apoi poți apăsa `Super + J` pentru a le stivui una peste alta, în loc să fie una lângă alta:

 ![navigation-stacked](images/navigation-stacked.webp)

Apasă din nou `Super + J` pentru a le readuce în pozițiile lor una lângă alta. Apoi încearcă `Super + Shift + Arrow Right` în timp ce ești pe browser, pentru a schimba ferestrele între ele.



 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Navighezi între ferestre pentru a o face activă pe cea pe care o vrei cu `Super + Arrow`. Aceasta va muta focalizarea și va duce cursorul în centrul noii aplicații.

Dacă apeși `Super + Shift + 2`, vei muta aplicația focalizată curent pe al doilea spațiu de lucru. `Super + Shift + 1` o aduce înapoi. (Iar `Super + Shift + Alt + 2` va muta aplicația focalizată curent pe al doilea spațiu de lucru, fără să comute la el).

Dacă ții apăsat `Super` și folosești mouse-ul pentru a face clic pe o fereastră, vei putea rearanja locul în care stă. Dacă ții apăsat `Super` și folosești butonul drept al mouse-ului, poți redimensiona liber fereastra.

Închizi o fereastră cu `Super + W` sau `Super + Q` (și închizi toate ferestrele cu `Ctrl + Alt + Delete`).

Poți trece și pe ecran complet cu `Super + F` sau doar pe lățimea completă (păstrând bara de sus) cu `Super + Alt + F` sau pe ecran complet în interiorul unei ferestre cu `Super + Ctrl + F` (bun pentru YouTube!).

### Dispunerea dwindle vs scrolling

Dispunerea implicită din Arch se numește dwindle. Ea păstrează vizibile în permanență toate ferestrele pe care le deschizi pe un singur spațiu de lucru, chiar dacă trebuie să le micșoreze.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Dar poți alege și să transformi un spațiu de lucru în dispunerea scrolling, în care ferestrele sunt aliniate una lângă alta, dincolo de marginea vizibilă a ecranului. Transformi un singur spațiu de lucru în această dispunere prin `Super + L`.


 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Alegerea este pentru fiecare spațiu de lucru în parte și rămâne. Așadar, poți păstra spațiul de lucru 1 pe dwindle pentru navigare și spațiul de lucru 2 pe scrolling pentru cod, iar ele vor reveni așa după o repornire.

Dacă vrei să folosești dispunerea scrolling ca implicită, poți seta asta în `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Gruparea ferestrelor

Ferestrele pot fi grupate folosind `Super + G`. Odată ce ești într-un grup, fiecare fereastră pe care o pornești cât timp acela este activ va aparține grupului. Te poți deplasa între aceste ferestre grupate folosind `Super + Ctrl + Arrow Left/Right` sau `Super + Alt + 1/2/3/4` pentru a merge direct la fereastra grupată, în ordine.

Poți scoate o fereastră din grupare cu `Super + Alt + G` sau poți desface întregul grup apăsând din nou `Super + G`. În sfârșit, poți muta ferestre din afara grupului în el cu `Super + Alt + Arrows`.

### Spațiul de lucru scratchpad

În sfârșit, există un spațiu de lucru scratchpad special, care coboară peste orice spațiu de lucru pe care te afli în prezent, cam ca o consolă Quake. Comută-l cu `Super + Grave` sau `Super + S` și așază acolo o fereastră folosind `Super + Shift + Grave` sau `Super + Alt + S`.

Funcționează deosebit de bine pentru un terminal care rulează un agent sau pentru comenzi cu care vrei să interacționezi rapid fără să părăsești spațiul de lucru curent. Pentru a muta o fereastră de pe scratchpad, trimite-o direct pe alt spațiu de lucru cu ceva de genul `Super + Shift + 1`.

Cât timp scratchpadul conține o singură fereastră, el coboară ca un panou centrat, în loc să se întindă pe tot ecranul. Pune o a doua aplicație pe el și va reveni la lățimea completă, astfel încât cele două să aibă loc să stea una lângă alta.

### Trebuie să te obișnuiești puțin!

Durează puțin până te obișnuiești să navighezi pe desktop așa, dar odată ce o faci, îți va fi greu să te întorci la o experiență tradițională de desktop, condusă cu mouse-ul!
