# Navegació

Tot a Arch passa per mitjà del teclat — _TOT!_ Quan el sistema arrenca per primera vegada, literalment no pots fer res només amb el ratolí. Però pots prémer `Super + Space` per mostrar el menú d'Arch i des d'aquí pots fer pràcticament de tot.

Però el menú d'Arch ni tan sols està pensat per ser la manera principal de fer funcionar el sistema la major part del temps. Podem anar més de pressa que això! Totes les aplicacions més importants estan vinculades directament a dreceres de teclat individuals. Inicies el terminal amb `Super + Return` i un navegador amb `Super + Shift + Return`. Prova de fer una cosa després de l'altra i veuràs la màgia de la disposició en mosaic de Hyprland en acció:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Després pots prémer `Super + J` per apilar-les una a sobre de l'altra en lloc de tenir-les de costat:

 ![navigation-stacked](images/navigation-stacked.webp)

Prem `Super + J` de nou per tornar-les a les posicions de costat. Després prova `Super + Shift + Arrow Right` mentre ets al navegador per intercanviar les finestres.



 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Et desplaces entre la finestra que vols que estigui activa amb `Super + Arrow`. Això canvia el focus i mou el cursor al centre de l'aplicació nova.

Si prems `Super + Shift + 2`, mouràs l'aplicació que té el focus actualment al segon espai de treball. `Super + Shift + 1` la torna a moure enrere. (I `Super + Shift + Alt + 2` mourà l'aplicació que té el focus actualment al segon espai de treball sense canviar a aquest espai).

Si mantens premuda `Super` i fas servir el ratolí per fer clic en una finestra, podràs reordenar on seu. Si mantens premuda `Super` i fas servir el botó dret del ratolí, pots redimensionar la finestra lliurement.

Tanques una finestra amb `Super + W` o `Super + Q` (i tanques totes les finestres amb `Ctrl + Alt + Delete`).

També pots passar a pantalla completa amb `Super + F` o fins i tot només a amplada completa (mantenint la barra superior) amb `Super + Alt + F` o a pantalla completa dins d'una finestra amb `Super + Ctrl + F` (ideal per a YouTube!).

### Disposició dwindle contra scrolling

La disposició predeterminada d'Arch s'anomena dwindle. Manté totes les finestres que obres en un sol espai de treball visibles en tot moment, encara que hagi de reduir-les.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Però també pots triar convertir un espai de treball en la disposició scrolling, on les finestres s'alineen de costat, més enllà de la vora visible de la pantalla. Converteixes un sol espai de treball en aquesta disposició per mitjà de `Super + L`.


 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

L'elecció és per espai de treball, i es manté. Així pots mantenir l'espai de treball 1 en dwindle per navegar i l'espai de treball 2 en scrolling per al codi, i tornaran d'aquesta manera després d'un reinici.

Si vols fer servir la disposició scrolling com a predeterminada, pots definir-ho a `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Agrupar finestres

Les finestres es poden agrupar amb `Super + G`. Un cop ets en un grup, totes les finestres que iniciïs mentre aquest està actiu pertanyeran al grup. Pots moure't entre aquestes finestres agrupades amb `Super + Ctrl + Arrow Left/Right` o `Super + Alt + 1/2/3/4` per anar directament a la finestra agrupada en ordre.

Pots moure una finestra fora de l'agrupació amb `Super + Alt + G` o desfer tot el grup prement `Super + G` de nou. Finalment, pots moure finestres de fora del grup cap a dins amb `Super + Alt + Arrows`.

### Espai de treball scratchpad

Finalment, hi ha un espai de treball especial scratchpad que cau sobre qualsevol espai de treball on siguis actualment, molt semblant a una consola Quake. Activa'l i desactiva'l amb `Super + Grave` o `Super + S`, i col·loca-hi una finestra amb `Super + Shift + Grave` o `Super + Alt + S`.

Funciona especialment bé per a un terminal que executa un agent, o per a controls amb què vols interactuar ràpidament sense deixar l'espai de treball actual. Per moure una finestra fora del scratchpad, envia-la directament a un altre espai de treball amb alguna cosa com `Super + Shift + 1`.

Mentre el scratchpad conté una sola finestra, cau com un tauler centrat en lloc d'estendre's per la pantalla. Posa-hi una segona aplicació i torna a l'amplada completa, perquè totes dues tinguin espai per seure de costat.

### Costa una mica acostumar-s'hi!

Costa una mica acostumar-se a navegar pel teu escriptori d'aquesta manera, però un cop ho facis, et costarà tornar a una experiència d'escriptori tradicional impulsada pel ratolí!
