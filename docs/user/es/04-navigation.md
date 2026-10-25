# Navegación

Todo en Arch sucede con el teclado — _¡TODO!_ Cuando el sistema arranca por primera vez, literalmente no puedes hacer nada solo con el mouse. Pero puedes presionar `Super + Space` para mostrar el menú de Arch y desde ahí hacer prácticamente todo.

Pero el menú de Arch ni siquiera está pensado para ser la forma principal de operar el sistema la mayor parte del tiempo. ¡Podemos hacerlo más rápido que eso! Todas las aplicaciones más importantes están vinculadas directamente a atajos de teclado individuales. Abres la terminal con `Super + Return` y un navegador con `Super + Shift + Return`. Prueba hacer una tras otra y verás la magia del mosaico de Hyprland en acción:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Luego puedes presionar `Super + J` para apilarlas una sobre otra en lugar de ponerlas lado a lado:

 ![navigation-stacked](images/navigation-stacked.webp)

Presiona `Super + J` otra vez para regresarlas a sus posiciones lado a lado. Luego prueba `Super + Shift + Arrow Right` estando en el navegador para intercambiar las ventanas.

Ahora prueba `Super + Ctrl + T` para abrir el monitor de actividad. Aparecerá como una ventana flotante. Puedes ponerla en mosaico con `Super + T` (y presionar eso otra vez para hacerla flotante de nuevo). Ahora presiona `Super + Shift + F` para abrir el administrador de archivos. Tendrás una ordenada configuración de cuatro ventanas:

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Navegas entre las ventanas hasta la que quieres que esté activa con `Super + Arrow`. Esto cambiará el foco y moverá el cursor al centro de la nueva aplicación.

Si presionas `Super + Shift + 2`, moverás la aplicación enfocada actualmente al segundo espacio de trabajo. `Super + Shift + 1` la regresa. (Y `Super + Shift + Alt + 2` moverá la aplicación enfocada actualmente al segundo espacio de trabajo sin cambiarte a él).

Si mantienes presionado `Super` y usas el mouse para hacer clic en una ventana, podrás reacomodar dónde queda. Si mantienes presionado `Super` y usas el botón derecho del mouse, puedes cambiar el tamaño de la ventana libremente.

Cierras una ventana con `Super + W` o `Super + Q` (y cierras todas las ventanas con `Ctrl + Alt + Delete`).

También puedes pasar a pantalla completa con `Super + F` o incluso solo a todo el ancho (manteniendo la barra superior) con `Super + Alt + F` o a pantalla completa dentro de una ventana con `Super + Ctrl + F` (¡ideal para YouTube!).

### Diseño dwindle vs. diseño con desplazamiento

El diseño predeterminado de Arch se llama dwindle. Mantiene visibles en todo momento todas las ventanas que abres en un mismo espacio de trabajo, aunque tenga que encogerlas.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Pero también puedes elegir convertir un espacio de trabajo al diseño con desplazamiento, donde las ventanas se alinean lado a lado, más allá del borde visible de la pantalla. Conviertes un espacio de trabajo individual a este diseño con `Super + L`.

Presionar `Super + L` otra vez vuelve flotante el espacio de trabajo, donde las ventanas se superponen libremente y tú las colocas, y una tercera vez lo regresa a dwindle. `Super + Alt + L` los recorre en el otro sentido. Una ventana que de por sí es flotante — una que desprendiste con `Super + T`, o una app que siempre se abre flotante — se mantiene flotante cuando el espacio de trabajo vuelve al mosaico. La barra superior marca el espacio de trabajo en el que estás con su diseño: un cuadrado para dwindle, un círculo para el diseño con desplazamiento y un triángulo para el flotante. Hacer clic en esa marca también alterna el diseño.

 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

La elección es por espacio de trabajo y se conserva. Así puedes mantener el espacio de trabajo 1 en dwindle para navegar y el espacio de trabajo 2 con desplazamiento para programar, y volverán así después de un reinicio.

Si quieres usar el diseño con desplazamiento como predeterminado, puedes configurar eso en `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Agrupar ventanas

Las ventanas se pueden agrupar con `Super + G`. Una vez que estás en un grupo, cada ventana que abras mientras eso está activo pertenecerá al grupo. Puedes moverte entre estas ventanas agrupadas con `Super + Ctrl + Arrow Left/Right` o con `Super + Alt + 1/2/3/4` para ir directamente a una ventana agrupada en orden.

Puedes sacar una ventana del grupo con `Super + Alt + G` o desarmar todo el grupo presionando `Super + G` otra vez. Por último, puedes mover ventanas fuera del grupo hacia dentro de él con `Super + Alt + Arrows`.

### Espacio de trabajo scratchpad

Por último, hay un espacio de trabajo especial tipo scratchpad que se despliega sobre cualquier espacio de trabajo en el que estés actualmente, muy parecido a una consola de Quake. Actívalo y desactívalo con `Super + Grave` o `Super + S`, y coloca una ventana ahí con `Super + Shift + Grave` o `Super + Alt + S`.

Funciona especialmente bien para una terminal que ejecuta un agente, o para controles con los que quieres interactuar rápido sin dejar el espacio de trabajo actual. Para sacar una ventana del scratchpad, envíala directamente a otro espacio de trabajo con algo como `Super + Shift + 1`.

Mientras el scratchpad contiene una sola ventana, se despliega como un panel centrado en lugar de abarcar toda la pantalla. Pon una segunda app en él y volverá a todo el ancho, para que las dos tengan espacio para estar lado a lado.

### ¡Cuesta un poco acostumbrarse!

Cuesta un poco acostumbrarse a navegar tu escritorio así, pero una vez que lo haces, ¡será difícil volver a una experiencia de escritorio tradicional basada en el mouse!
