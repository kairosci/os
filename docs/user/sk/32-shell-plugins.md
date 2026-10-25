# Pluginy shellu

Pracovná plocha Arch beží ako jeden dlho žijúci proces Quickshell s názvom `arch-shell` a takmer všetko, čo vidíš na obrazovke, je plugin vnútri neho. Lišta je plugin. Rovnako panely, ktoré z nej padajú, celoobrazovkové prekrytia ako výber emoji a správca schránky, samotné menu Arch, zamykacia obrazovka, dialóg polkit a bezhlavé služby, ktoré sledujú tvoju batériu a v noci zohrievajú tvoju obrazovku.

To nie je len detail implementácie. To znamená, že môžeš vypnúť časti pracovnej plochy, vymeniť ich alebo napísať vlastné bez toho, aby si sa dotkol jediného riadka zdrojového kódu Arch.

Pluginy prvej strany sa dodávajú s Arch a žijú v `$ARCH_PATH/src/shell/plugins/`. Všetko, čo pridáš sám — vlastné experimenty alebo niečo, čo si našiel na GitHube — žije v `~/.config/arch/plugins/`. Oba sa zisťujú rovnakým spôsobom pri spustení, ale zabudované získavajú dôveryhodné rozhrania shellu, zatiaľ čo pluginy tretích strán získavajú obmedzené rozhranie obmedzené na ich vlastnú službu a životný cyklus. Klony zabudovaných si zachovávajú len konfiguráciu špecifickú pre zdroj a volania používateľského rozhrania potrebné pre pôvodné správanie.

## Zobrazenie toho, čo máš

```
arch plugin list
```

Tým sa vypíše každý zistený plugin s jeho id, či je zapnutý, či je prvej alebo tretej strany, jeho druhmi a jeho zobrazovaným názvom. Pridaj `--json`, ak ho posúvaš niečomu inému.

Id pluginov sú v menných priestoroch. Zabudované sa všetky začínajú reťazcom `arch.` — `arch.clock`, `arch.network`, `arch.notifications` — a tento menný priestor je vyhradený, takže plugin tretej strany si ho nikdy nemôže nárokovať.

## Zapínanie a vypínanie

```
arch plugin enable arch.tailscale
arch plugin disable arch.weather
```

Alebo použi menu: _Nastavenie > Pluginy_ má položky Zapnúť, Vypnúť, Pridať, Klonovať a Odstrániť, každú s výberom, ktorý ponúka len pluginy, ktoré majú pre danú akciu zmysel.

Stav zapnutia je uložený v `~/.config/arch/shell.json` a pravidlo sa pre tieto dva druhy pluginov mierne líši. Plugin tretej strany je zapnutý presne vtedy, keď sa jeho id objaví niekde v tomto súbore — ako položka rozloženia lišty, ako položka v `plugins[]` alebo ako `bar.id`. Pluginy prvej strany, ktoré nie sú widgetmi lišty, fungujú opačne: predvolene sú zapnuté a vypnú sa len uvedením v `disabledPlugins[]`.

Plný plugin lišty vôbec nemá stav vypnutia. Vždy existuje presne jedna lišta, takže ju nahradíš zapnutím inej. Umiestnenie widgetov lišty je popísané v časti [horná lišta](05-the-top-bar.md).

## Pridanie pluginu z gitu

Plugin tretej strany je len git repozitár so súborom `manifest.json` v koreňovom adresári.

```
arch plugin add https://github.com/acme/arch-weather.git --enable
```

Skôr než niečo urobí, jasne ti povie, že pluginy bežia ako ľubovoľný, nesandboxovaný kód vnútri tvojho dlho žijúceho procesu shellu, ukáže ti URL a požiada ťa o potvrdenie. Ber to vážne. Rozhranie pluginov tretích strán priamo nesprístupňuje autentifikačné služby a náhradná lišta získava len obmedzené možnosti pre nakonfigurované neautentifikačné používateľské rozhranie. Vizuálne pluginy stále zdieľajú scénu QML shellu a môžu prechádzať bežnými rodičovskými objektmi, zatiaľ čo všetok kód pluginov beží so všetkým, na čo sa môže dostať tvoj používateľský účet. Stav overovania je chránený samostatne tak, že sa tieto služby uchovávajú mimo dosiahnuteľného grafu hostiteľských objektov. Pridávaj len repozitáre, ktoré si ochotný spustiť, a prečítaj si ich, skôr než ich zapneš.

Náhradná lišta môže vykresľovať nainštalované widgety, ale widgety tretích strán podporované službami tam môžu mať obmedzenú funkcionalitu, pretože lišta nesmie požadovať živý objekt služby iného pluginu. Prepni späť na zabudovanú `arch.bar`, ak takýto widget potrebuje svoju sprievodnú službu.

Potom repozitár naklonuje do prípravného (staging) adresára, overí manifest, odmietne inštaláciu, ak si toto id už nárokuje iný plugin, a presunie ho do `~/.config/arch/plugins/<id>/`. Bez príznaku `--enable` sa spýta, či ho chceš zapnúť teraz, a môžeš povedať nie a najprv si prejsť kód. Nikdy z pluginu nič nespustí, nikdy nevykoná inštalačný hák a nikdy si nevyžiada sudo — klonuje súbory, skontroluje manifest a prostredníctvom IPC prepne bit.

Aktualizácia je „fast-forward pull“ tohto istého checkoutu:

```
arch plugin update acme.weather
arch plugin update
```

Bez id aktualizuje každý gitom spravovaný plugin, ktorý máš. Pred použitím ti ukáže diff, odmietne aktualizovať, ak máš lokálne zmeny, cez ktoré nemôže urobiť fast-forward, a vráti zmeny späť, ak nová revízia zlyhá pri overovaní.

```
arch plugin remove acme.weather
```

Odstránenie plugin najprv vypne a potom ho odstráni, ak ide o git checkout (repozitár je stále upstream), alebo ho odlinkuje, ak ide o symbolický odkaz. Ručne vytvorený priečinok pluginu bez git repozitára sa presunie do zálohy s časovou pečiatkou vnútri adresára pluginov, namiesto toho, aby sa úplne odstránil.

## Klonovanie zabudovaného pluginu na jeho úpravu

Toto je moja obľúbená časť. Ak chceš zmeniť, ako sa správa zabudovaný widget, neupravuj súbory pod `$ARCH_PATH` — patria balíčku a ďalšia aktualizácia ich prepíše. Namiesto toho ho naklonuj:

```
arch plugin clone arch.clock
```

Tým sa celý plugin skopíruje do `~/.config/arch/plugins/dhh.clock` (tvoje používateľské meno, nie moje), premenuje sa na „My Clock“, zapne sa a shell sa prepne zo zabudovaného na tvoju kópiu — pričom sa zachová poloha a nastavenia existujúceho widgetu lišty. Pridaj príznak `--edit` a nový adresár sa okamžite otvorí v tvojom `$EDITOR`, čo pre teba robí položka menu _Nastavenie > Pluginy > Klonovať plugin_.

Prefix používateľského mena udržuje id tvojho klonu tvoje, takže jeho zdieľanie nebude kolidovať s cudzím. Volania na pôvodné zabudované id sa smerujú do tvojho klonu, takže nič, čo odkazovalo na `arch.clock`, nepotrebuje aktualizáciu. A ak v ňom narobíš neporiadok, `arch plugin remove dhh.clock` vráti zabudovaný späť.

Uloženie súboru kdekoľvek pod `~/.config/arch/plugins/` automaticky znova načíta kód pluginu, takže môžeš nechať editor otvorený a sledovať, ako tvoje zmeny pristávajú.

## Písanie vlastného pluginu

Plugin je adresár so súborom `manifest.json` a nejakým QML. Manifest deklaruje `schemaVersion: 1`, `id`, `name`, `version`, jeden alebo viacero druhov (`kinds`) a objekt `entryPoints`, ktorý ukazuje na súbor QML pre každý druh:

| Druh | Čo to je |
|------|------------|
| `bar-widget` | Komponent, ktorý môže aktívna lišta vložiť do sekcie |
| `panel` | Trvalé alebo vyvolávané plávajúce okno |
| `overlay` | Celoobrazovkové prekrytie |
| `menu` | Vyvolávaná plocha menu |
| `service` | Bezhlavý singleton bez používateľského rozhrania |
| `bar` | Plná lišta, ktorá nahrádza zabudovanú |

Plugin môže deklarovať niekoľko druhov naraz — mediálny plugin je `service` aj `bar-widget`. Widgety lišty získavajú ďalší blok `barWidget` so zobrazovaným názvom, kategóriou, voliteľným `defaultSection` a `allowMultiple`, čo hovorí, či má zmysel mať ich na lište viac než jeden. Väčšina widgetov to nastavuje na `false`; rozpery a indikátory to nastavujú na `true`.

Skôr než niečo zverejníš, skontroluj to:

```
arch plugin validate ./my-plugin
```

Tým sa spustia tie isté kontroly, ktoré shell vykonáva pri načítavaní: verzia schémy, povinné polia, id, ktoré nie je vyhradené, vstupné body, ktoré sú bezpečnými relatívnymi cestami a skutočne existujú, vstupný bod pre každý druh, ktorý si deklaroval, a žiadne symbolické odkazy kdekoľvek vnútri priečinka.

Informácie o vývoji pluginov nájdeš v [referencii shellu](https://github.com/kairosci/arch) a v [katalógu pluginov prvej strany](https://github.com/kairosci/arch).

## Zdieľanie svojho pluginu so svetom

Keď vytvoríš niečo, čo sa ti páči, umiestni to do verejného git repozitára. To je celý distribučný mechanizmus — ktokoľvek potom môže spustiť `arch plugin add` na tvoju URL a mať to spustené za pár sekúnd.

Aby ľudia tvoj plugin skutočne našli, uveď ho na [plugins.github.com/kairosci/arch](https://plugins.github.com/kairosci/arch). To je trh s pluginmi shellu Arch a prvé miesto, kam sa pozrieť, keď rozmýšľaš, či už niekto vytvoril widget, ktorý sa chystáš napísať. Skôr než začneš, prezri si to!
