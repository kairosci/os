# Shell-Plugins

Der Arch-Desktop läuft als ein einziger langlebiger Quickshell-Prozess namens `arch-shell`, und fast alles, was du auf dem Bildschirm siehst, ist ein Plugin darin. Die Leiste ist ein Plugin. Ebenso die Panels, die aus ihr herunterklappen, die Vollbild-Overlays wie Emoji-Auswahl und Zwischenablagen-Manager, das Arch-Menü selbst, der Sperrbildschirm, der polkit-Dialog und die kopflosen Dienste, die deinen Akku beobachten und deinen Bildschirm nachts aufwärmen.

Das ist nicht nur ein Implementierungsdetail. Es bedeutet, dass du Teile des Desktops ausschalten, austauschen oder eigene schreiben kannst, ohne eine Zeile von Archs Quellcode zu berühren.

Die eigenen Plugins werden mit Arch ausgeliefert und leben in `$ARCH_PATH/src/shell/plugins/`. Alles, was du selbst hinzufügst — deine eigenen Experimente oder etwas, das du auf GitHub gefunden hast — lebt in `~/.config/arch/plugins/`. Beide werden beim Start auf dieselbe Weise erkannt, aber Eingebaute erhalten vertrauenswürdige Shell-Schnittstellen, während Drittanbieter-Plugins eine begrenzte Schnittstelle erhalten, die auf ihren eigenen Dienst und Lebenszyklus beschränkt ist. Klone von Eingebauten behalten nur die quellenspezifischen Konfigurations- und UI-Aufrufe, die für das ursprüngliche Verhalten nötig sind.

## Sehen, was du hast

```
arch plugin list
```

Das gibt jedes entdeckte Plugin mit seiner ID aus, ob es aktiviert ist, ob es eigen oder Drittanbieter ist, seine Arten und seinen Anzeigenamen. Füge `--json` hinzu, wenn du es an etwas anderes fütterst.

Plugin-IDs liegen in Namensräumen. Die Eingebauten beginnen alle mit `arch.` — `arch.clock`, `arch.network`, `arch.notifications` — und dieser Namensraum ist reserviert, sodass ein Drittanbieter-Plugin ihn niemals beanspruchen kann.

## Sie ein- und ausschalten

```
arch plugin enable arch.tailscale
arch plugin disable arch.weather
```

Oder verwende das Menü: _Einrichtung > Plugins_ hat Enable, Disable, Add, Clone und Remove, jeweils mit einer Auswahl, die nur die Plugins anbietet, die für diese Aktion sinnvoll sind.

Der Aktiviert-Zustand wird in `~/.config/arch/shell.json` gespeichert, und die Regel unterscheidet sich für die beiden Plugin-Arten leicht. Ein Drittanbieter-Plugin ist genau dann aktiviert, wenn seine ID irgendwo in dieser Datei erscheint — als Eintrag im Leistenlayout, als Eintrag in `plugins[]` oder als `bar.id`. Eigene Plugins, die keine Leisten-Widgets sind, verhalten sich umgekehrt: Sie sind standardmäßig an und schalten sich nur ab, indem sie in `disabledPlugins[]` aufgeführt werden.

Ein vollwertiges Leisten-Plugin hat überhaupt keinen Aus-Zustand. Es gibt immer genau eine Leiste, sodass du sie ersetzt, indem du eine andere aktivierst. Die Platzierung von Leisten-Widgets wird in [der Menüleiste](05-the-top-bar.md) behandelt.

## Ein Plugin aus Git hinzufügen

Ein Drittanbieter-Plugin ist einfach ein Git-Repo mit einer `manifest.json` in seiner Wurzel.

```
arch plugin add https://github.com/acme/arch-weather.git --enable
```

Bevor es irgendetwas tut, sagt es dir unverblümt, dass Plugins als beliebiger, nicht-sandboxierter Code in deinem langlebigen Shell-Prozess laufen, zeigt dir die URL und bittet dich um Bestätigung. Nimm das ernst. Die Schnittstelle für Drittanbieter-Plugins legt Authentifizierungsdienste nicht direkt offen, und eine Ersatzleiste erhält nur begrenzte Fähigkeiten für konfigurierte Nicht-Authentifizierungs-UI. Visuelle Plugins teilen sich weiterhin die QML-Szene der Shell und können gewöhnliche Elternobjekte durchwandern, während der gesamte Plugin-Code mit allem läuft, was dein Benutzerkonto erreichen kann. Der Authentifizierungszustand wird separat geschützt, indem diese Dienste außerhalb des erreichbaren Host-Objektgrafen gehalten werden. Füge nur Repos hinzu, die du bereit bist auszuführen, und lies sie, bevor du sie aktivierst.

Eine Ersatzleiste kann installierte Widgets rendern, aber dienstgestützte Drittanbieter-Widgets können dort eingeschränkte Funktionalität haben, weil die Leiste das Live-Dienstobjekt eines anderen Plugins nicht anfordern darf. Wechsle zur eingebauten `arch.bar` zurück, wenn ein solches Widget seinen Begleitdienst benötigt.

Dann klont es das Repo in ein Staging-Verzeichnis, validiert das Manifest, verweigert die Installation, wenn ein anderes Plugin diese ID bereits beansprucht, und verschiebt es nach `~/.config/arch/plugins/<id>/`. Ohne `--enable` fragt es, ob du es jetzt anschalten willst, und du kannst Nein sagen und zuerst den Code lesen. Es führt niemals etwas aus dem Plugin aus, führt niemals einen Installations-Hook aus und fragt niemals nach sudo — es klont Dateien, prüft das Manifest und schaltet ein Bit per IPC um.

Aktualisieren ist ein Fast-Forward-Pull desselben Checkouts:

```
arch plugin update acme.weather
arch plugin update
```

Ohne ID aktualisiert es jedes git-verwaltete Plugin, das du hast. Es zeigt dir das Diff vor dem Anwenden, verweigert die Aktualisierung, wenn du lokale Änderungen hast, an denen es nicht per Fast-Forward vorbei kann, und rollt zurück, wenn die neue Revision die Validierung nicht besteht.

```
arch plugin remove acme.weather
```

Das Entfernen deaktiviert das Plugin zuerst und löscht es dann, wenn es ein Git-Checkout ist (das Repo ist weiterhin upstream), oder löst die Verknüpfung, wenn es ein Symlink ist. Ein handgemachter Plugin-Ordner ohne Git-Repo wird stattdessen in ein zeitgestempeltes Backup innerhalb des Plugins-Verzeichnisses verschoben, statt ganz gelöscht zu werden.

## Ein Eingebautes klonen, um es zu ändern

Das ist mein Lieblingsteil. Wenn du ändern willst, wie sich ein eingebautes Widget verhält, bearbeite nicht die Dateien unter `$ARCH_PATH` — diese gehören zum Paket, und die nächste Aktualisierung wird sie überschreiben. Klone es stattdessen:

```
arch plugin clone arch.clock
```

Das kopiert das ganze Plugin nach `~/.config/arch/plugins/dhh.clock` (dein Benutzername, nicht meiner), benennt es in „My Clock“ um, aktiviert es und schaltet die Shell vom Eingebauten auf deine Kopie um — unter Beibehaltung der Position und Einstellungen eines bestehenden Leisten-Widgets. Füge `--edit` hinzu, um das neue Verzeichnis sofort in deinem `$EDITOR` zu öffnen, was das Menü _Einrichtung > Plugins > Clone Plugin_ für dich tut.

Das Benutzername-Präfix hält die ID deines Klons zu deiner, sodass das Teilen nicht mit der von jemand anderem kollidiert. Aufrufe an die ursprüngliche eingebaute ID werden an deinen Klon weitergeleitet, sodass nichts, was sich auf `arch.clock` bezog, aktualisiert werden muss. Und wenn du es durcheinanderbringst, stellt `arch plugin remove dhh.clock` das Eingebaute wieder her.

Das Speichern einer Datei unter `~/.config/arch/plugins/` lädt den Plugin-Code automatisch neu, sodass du den Editor offen lassen und deinen Änderungen beim Landen zusehen kannst.

## Eigenes schreiben

Ein Plugin ist ein Verzeichnis mit einer `manifest.json` und etwas QML. Das Manifest deklariert `schemaVersion: 1`, eine `id`, `name`, `version`, eine oder mehrere `kinds` und ein Objekt `entryPoints`, das für jede Art auf die QML-Datei zeigt:

| Kind | What it is |
|------|------------|
| `bar-widget` | Eine Komponente, die die aktive Leiste in einen Abschnitt fallen lassen kann |
| `panel` | Ein dauerhaftes oder herbeigerufenes schwebendes Fenster |
| `overlay` | Ein Vollbild-Overlay |
| `menu` | Eine herbeigerufene Menüoberfläche |
| `service` | Ein kopfloses Singleton ohne UI |
| `bar` | Eine vollständige Leiste, die die eingebaute ersetzt |

Ein Plugin kann mehrere Arten auf einmal deklarieren — das Medien-Plugin ist sowohl ein `service` als auch ein `bar-widget`. Leisten-Widgets erhalten einen zusätzlichen Block `barWidget` mit einem Anzeigenamen, einer Kategorie, einer optionalen `defaultSection` und `allowMultiple`, was angibt, ob es sinnvoll ist, mehr als eines in der Leiste zu haben. Die meisten Widgets setzen es auf `false`; Abstandshalter und Anzeigen setzen es auf `true`.

Bevor du etwas veröffentlichst, prüfe es:

```
arch plugin validate ./my-plugin
```

Das führt dieselben Prüfungen aus wie die Shell beim Laden: die Schemaversion, die Pflichtfelder, eine ID, die nicht reserviert ist, Einstiegspunkte, die sichere relative Pfade sind und tatsächlich existieren, einen Einstiegspunkt für jede beanspruchte Art und keine Symlinks irgendwo im Ordner.

Zur Plugin-Entwicklung siehe die [Shell-Referenz](https://github.com/kairosci/os) und den [Katalog eigener Plugins](https://github.com/kairosci/os).

## Deines mit der Welt teilen

Sobald du etwas gemacht hast, das dir gefällt, lege es in ein öffentliches Git-Repo. Das ist der gesamte Vertriebsmechanismus — jeder kann dann `arch plugin add` gegen deine URL ausführen und es innerhalb von Sekunden laufen haben.

Um Menschen zu helfen, es tatsächlich zu finden, trage es auf [plugins.github.com/kairosci/os](https://plugins.github.com/kairosci/os) ein. Das ist der Marktplatz für Arch-Shell-Plugins und der erste Ort, an dem du nachsehen solltest, wenn du dich fragst, ob jemand das Widget, das du gerade schreiben willst, schon gebaut hat. Stöbere dort, bevor du anfängst!
