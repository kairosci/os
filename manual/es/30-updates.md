# Actualizaciones

Arch y tus paquetes se mantienen actualizados mediante _Actualizar > Arch_ en el menú de Arch (`Super + Space`).

Arch mismo se instala como paquetes normales de pacman desde el [Repositorio de paquetes de Arch](https://github.com/kairosci/arch), así que una actualización instala [la última versión de Arch](https://github.com/kairosci/arch), ejecuta cualquier migración pendiente para poner tu sistema en sincronía con lo más reciente, y actualiza todos los paquetes del sistema desde el [Mirror de Arch de Arch](https://github.com/kairosci/arch) y el [AUR](https://aur.archlinux.org/) (si has instalado algún paquete del AUR).

Cuando se publiquen nuevas versiones, aparecerá un ícono de flecha circular a la derecha de tu reloj. Haz clic en él y el proceso de actualización comenzará.

![update-available](images/update-available.webp)

### Cuatro canales

Arch se actualiza por cuatro canales: stable, RC, edge y dev. Las instalaciones nuevas empiezan en el canal stable, que sigue las [versiones oficiales](https://github.com/kairosci/arch), así como el [mirror estable de Arch de Arch](https://github.com/kairosci/arch) que va un mes detrás de lo más reciente, para que podamos detectar cualquier incompatibilidad nueva que requiera cambios de configuración antes de que cause problemas a la gente.

Pero si quieres ayudar a detectar esos posibles problemas, puedes usar el canal edge. Eso mantendrá tus paquetes de Arch siguiendo las últimas compilaciones de desarrollo, y te permite actualizar a los últimos paquetes de Arch en cuanto estén disponibles. Solo deberías hacer esto si tienes experiencia con Linux y sabes cómo recuperar un sistema que tiene problemas.

Antes de cualquier nueva versión mayor, haremos la validación final usando el canal RC. Si te interesa ayudar con el pulido final, ven a pasar el rato en #arch-release-candidates en el Discord.

Por último, está el canal dev, que vincula Arch directamente a una copia git del código fuente en `~/arch`, combinada con los paquetes edge. Solo deberías usar este canal si eres un usuario experimentado de Linux, trabajas directamente en Arch y estás dispuesto a tolerar que algo se rompa.

Puedes cambiar entre canales usando _Actualizar > Canal_ desde el menú de Arch (o `arch-channel-set` en la terminal).

### Actualizaciones de firmware

Tus paquetes no son lo único que se queda viejo. Muchas laptops y periféricos distribuyen firmware de BIOS, SSD y dock mediante el Linux Vendor Firmware Service, y _Actualizar > Firmware_ en el menú de Arch obtendrá e instalará lo que tu hardware tenga esperando. Instala `fwupd` la primera vez que lo ejecutas. Mucho firmware solo se puede escribir durante un reinicio, así que no te sorprendas si te piden uno.

### Advertencia sobre actualizaciones directas con pacman/yay

Si ya estás familiarizado con Arch, podrías tener la tentación de simplemente ejecutar `pacman -Syu` o `yay -Syu` por tu cuenta, pero si haces eso, te perderás la instantánea, las migraciones y las actualizaciones de configuración que Arch ejecuta junto con los paquetes nuevos. Por eso Arch en realidad detendrá una actualización directa del sistema y te dirigirá a `archctl update` en su lugar. (Si de verdad sabes lo que haces, la protección te dirá cómo omitirla para una sola transacción).

### Revertir actualizaciones malas

Si alguna vez tienes un problema después de hacer una actualización, puedes revertir tu sistema a la instantánea tomada antes de la actualización. Solo reinicia y elige en el menú de arranque la instantánea de antes de que empezaras la actualización.

![bootloader](images/bootloader.webp)

Si de algún modo tus archivos de configuración se han corrompido, también puedes realizar una reinstalación de Arch usando `arch reinstall` en la terminal. Esto reinstalará todos los paquetes predeterminados de Arch, te pondrá en stable y bajará de versión cualquier paquete que sea demasiado nuevo, y restablecerá todos los archivos de configuración. ¡Ten en cuenta que al hacer esto se sobrescribirán todos tus cambios de configuración de usuario sobre los valores predeterminados de Arch!
