# Avis

## Notifications

Les avis affichent des informations ponctuelles sans ouvrir de panneau. Les codes de vérification peuvent être copiés sans entrer dans l’[historique du presse-papiers](08-unified-clipboard-history.md), puis sont effacés après une minute. Les liens présents dans un avis peuvent être ouverts d’un clic.

L’historique est conservé pendant une journée. Pour modifier cette durée, réglez `historyHours` dans la section `notifications` de `~/.config/arch/shell.json` : `1` pour une heure, `168` pour une semaine ou `0` pour ne rien conserver sur le disque.

## Avis par raccourci clavier

Les raccourcis suivants affichent rapidement la date et l’heure, l’état de la batterie ou la météo actuelle.

### Date et heure

`Super + Ctrl + Alt + T`

 ![notice-datetime](images/notice-datetime.webp)

### Météo

`Super + Ctrl + Alt + W`

 ![notice-weather](images/notice-weather.webp)

L'emplacement est détecté à partir de votre adresse IP, ce qui est généralement assez proche, mais pas toujours. Vous pouvez le préciser avec `arch weather location --set Malibu`, ou être exact en ajoutant des coordonnées : `arch weather location --set Malibu 34.0259,-118.7798`. Exécutez `arch weather location` tout seul pour voir où il pense que vous êtes, et `--clear` pour revenir à la détection automatique.

### Batterie

`Super + Ctrl + Alt + B`

 ![notice-battery](images/notice-battery.webp)
