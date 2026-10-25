# Navigation

Tout dans Arch se fait au clavier — _TOUT !_ Lorsque le système démarre pour la première fois, vous ne pouvez littéralement rien faire avec la souris seule. Mais vous pouvez appuyer sur `Super + Space` pour afficher le Arch Menu et, à partir de là, faire à peu près tout.

Mais le menu Arch n'est même pas censé être le principal moyen d'utiliser le système la plupart du temps. Nous pouvons faire plus rapide ! Toutes les applications les plus importantes sont directement liées à des touches de raccourci individuelles. Vous lancez le terminal avec `Super + Return` et un navigateur avec `Super + Shift + Return`. Essayez de faire l'un après l'autre, et vous verrez la magie du tuilage de Hyprland en action :

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Vous pouvez ensuite appuyer sur `Super + J` pour les empiler l'un au-dessus de l'autre au lieu de les mettre côte à côte :

 ![navigation-stacked](images/navigation-stacked.webp)

Appuyez à nouveau sur `Super + J` pour les remettre côte à côte. Essayez ensuite `Super + Shift + Arrow Right` depuis le navigateur pour échanger les fenêtres.

Essayez maintenant `Super + Ctrl + T` pour lancer le moniteur d'activité. Il apparaîtra sous forme de fenêtre flottante. Vous pouvez la tuiler avec `Super + T` (et appuyer à nouveau dessus pour la rendre à nouveau flottante). Appuyez maintenant sur `Super + Shift + F` pour ouvrir le gestionnaire de fichiers. Vous obtiendrez une jolie configuration en quatre parties :

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Vous naviguez entre les fenêtres pour choisir celle qui doit être active avec `Super + Arrow`. Cela changera le focus et déplacera le curseur au centre de la nouvelle application.

Si vous appuyez sur `Super + Shift + 2`, vous déplacerez l'application actuellement active vers le deuxième espace de travail. `Super + Shift + 1` la ramène. (Et `Super + Shift + Alt + 2` déplacera l'application actuellement active vers le deuxième espace de travail sans basculer dessus).

Si vous maintenez `Super` enfoncée et utilisez la souris pour cliquer sur une fenêtre, vous pourrez réorganiser sa position. Si vous maintenez `Super` et utilisez le bouton droit de la souris, vous pouvez redimensionner librement la fenêtre.

Vous fermez une fenêtre avec `Super + W` ou `Super + Q` (et fermez toutes les fenêtres avec `Ctrl + Alt + Delete`).

Vous pouvez également passer en plein écran avec `Super + F`, ou même simplement en pleine largeur (en conservant la barre supérieure) avec `Super + Alt + F`, ou en plein écran à l'intérieur d'une fenêtre avec `Super + Ctrl + F` (parfait pour YouTube !).

### Disposition dwindle vs disposition défilante

La disposition par défaut de Arch s'appelle dwindle. Elle garde toutes les fenêtres que vous ouvrez sur un même espace de travail visibles en permanence, même si elle doit les réduire.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Mais vous pouvez aussi choisir de transformer un espace de travail en disposition défilante, où les fenêtres sont alignées côte à côte, au-delà du bord visible de l'écran. Vous transformez un seul espace de travail dans cette disposition via `Super + L`.

Appuyer à nouveau sur `Super + L` rend l'espace de travail flottant, où les fenêtres se chevauchent librement et où vous les placez vous-même, et une troisième pression le ramène à dwindle. `Super + Alt + L` les parcourt dans l'autre sens. Une fenêtre qui flotte de toute façon — une que vous avez détachée avec `Super + T`, ou une application qui s'ouvre toujours en mode flottant — continue de flotter lorsque l'espace de travail repasse en tuilage. La barre supérieure marque l'espace de travail sur lequel vous vous trouvez avec sa disposition : un carré pour dwindle, un cercle pour le défilement et un triangle pour le flottant. Cliquer sur cette marque fait également défiler les dispositions.

 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Le choix se fait par espace de travail, et il persiste. Vous pouvez donc garder l'espace de travail 1 en dwindle pour la navigation et l'espace de travail 2 en défilement pour le code, et ils reviendront ainsi après un redémarrage.

Si vous souhaitez utiliser la disposition défilante par défaut, vous pouvez le définir dans `~/.config/hypr/looknfeel.lua` :

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Grouper les fenêtres

Les fenêtres peuvent être groupées à l'aide de `Super + G`. Une fois que vous êtes dans un groupe, chaque fenêtre que vous lancez tant que celui-ci est actif appartiendra au groupe. Vous pouvez vous déplacer entre ces fenêtres groupées à l'aide de `Super + Ctrl + Arrow Left/Right` ou `Super + Alt + 1/2/3/4` pour aller directement à une fenêtre groupée dans l'ordre.

Vous pouvez sortir une fenêtre du groupe avec `Super + Alt + G` ou dissoudre l'ensemble du groupe en appuyant à nouveau sur `Super + G`. Enfin, vous pouvez déplacer des fenêtres extérieures au groupe vers celui-ci avec `Super + Alt + Arrows`.

### Espace de travail scratchpad

Enfin, il existe un espace de travail scratchpad spécial qui descend par-dessus l'espace de travail sur lequel vous vous trouvez actuellement, un peu comme une console Quake. Activez-le avec `Super + Grave` ou `Super + S`, et placez-y une fenêtre à l'aide de `Super + Shift + Grave` ou `Super + Alt + S`.

Il fonctionne particulièrement bien pour un terminal exécutant un agent, ou pour des contrôles avec lesquels vous voulez interagir rapidement sans quitter l'espace de travail actuel. Pour déplacer une fenêtre hors du scratchpad, envoyez-la directement vers un autre espace de travail avec quelque chose comme `Super + Shift + 1`.

Tant que le scratchpad ne contient qu'une seule fenêtre, il descend sous forme de panneau centré plutôt que de couvrir tout l'écran. Mettez-y une deuxième application et il repasse en pleine largeur, afin que les deux aient de la place pour être côte à côte.

### Il faut un peu de temps pour s'y habituer !

Il faut un peu de temps pour s'habituer à naviguer sur votre bureau de cette manière, mais une fois que vous y serez habitué, il sera difficile de revenir à une expérience de bureau traditionnelle pilotée à la souris !
