# Guía de usuario de Arctiva

> English version: [../../en/user/README.md](../../en/user/README.md)

Arctiva es una distribución Linux basada en Arch Linux, con el escritorio KDE Plasma al estilo de Windows. Esta guía es para quien nunca ha instalado Linux.

**Estado:** versión de pruebas. Aún no hay una ISO pública para descargar; cuando la haya, estará en la página de *Releases* del repositorio, con su suma y su firma (ver [publicación](../publicacion.md)).

## 1. Qué necesitas

- Un equipo con **UEFI** (casi todos los de los últimos 10 años; Arctiva no arranca en modo BIOS antiguo).
- **4 GiB de RAM** como mínimo y **25 GiB libres** de disco.
- Un USB de 4 GB o más (se borra por completo).
- Conexión a internet durante la instalación (para lo que no cabe en la ISO, como el kernel LTS o los perfiles Juegos y Oficina). Sin conexión se instala igual lo que trae la ISO. Algunas aplicaciones básicas (Kate, Ark, Okular, Gwenview, Spectacle y KWalletManager) no vienen en la ISO para que pese menos: se descargan al instalar y, si no hay conexión, se instalan solas **la primera vez que te conectes a Internet**, junto con las actualizaciones del sistema. Una notificación te avisa de lo pendiente, de cuándo empieza y de cuándo termina.

## 2. Preparar el USB

Descarga la ISO y comprueba que es auténtica (ver [publicación](../publicacion.md)). Después, con uno de estos programas:

- **Rufus** (Windows): elige la ISO, el esquema de partición **GPT** y el sistema de destino **UEFI**.
- **balenaEtcher** (Windows, macOS, Linux): elige la ISO y el USB.
- **Ventoy** (Windows, Linux): copia la ISO al USB ya preparado con Ventoy. En su menú elige **«Boot in grub2 mode»**: el modo normal se queda en un shell de emergencia y todavía no arranca Arctiva. Si tienes dudas, usa Rufus o Etcher.
- **dd** (Linux): `sudo dd if=arctiva-X.Y.Z-x86_64.iso of=/dev/sdX bs=4M status=progress oflag=sync` (cuidado: `/dev/sdX` es el USB, no tu disco).

## 3. Antes de arrancar: Secure Boot y BitLocker

- **Secure Boot** (D-05): Arctiva **no** arranca con Secure Boot activado. Entra en la configuración del firmware (UEFI/BIOS; suele ser Supr, F2 o F12 al encender) y desactívalo.
- **BitLocker (Windows):** si vas a instalar **junto a Windows** y Windows usa BitLocker (o «cifrado del dispositivo»), **ten a mano la clave de recuperación** de tu cuenta Microsoft: Windows la pedirá al cambiar la configuración de arranque. Reduce la partición de Windows desde la *Administración de discos* de Windows y apaga Windows del todo (el *inicio rápido* deja el disco en un estado que impide redimensionarlo).
- Haz **copia de seguridad** de lo importante. Instalar siempre tiene algún riesgo.

## 4. Arrancar e instalar

1. Arranca desde el USB (menú de arranque del firmware, suele ser F12 o F8) y elige «Arctiva (live)». Si la pantalla sale mal, prueba «safe graphics». Arrancar desde un USB puede tardar uno o dos minutos: espera al escritorio.
2. Pruébalo sin instalar: es una sesión en vivo completa. Se abre una ventana de bienvenida con el botón **Instalar Arctiva**, y el mismo icono está en el escritorio. No cambia nada en tu disco hasta que ejecutes el instalador.
3. Sigue el instalador: idioma, zona horaria y teclado; el **perfil** (Básico, Juegos u Oficina; con Ctrl+clic eliges varios); la página **Comprobación**, que avisa de Windows hibernado, BitLocker, batería y red; el **disco** (borrar todo, **instalar junto a otro sistema** o reemplazar una partición); y tu usuario y contraseña.
4. Si particionas a mano, haz la raíz **Btrfs**: las instantáneas (apartado 6) la necesitan y el instalador no te avisa. En la página del disco, **cifrar el sistema** es opcional. Si lo activas, al arrancar GRUB te pedirá la contraseña **en modo texto** antes de mostrar nada más: es normal.
5. Revisa el **resumen** y pulsa Instalar. Al terminar, reinicia y quita el USB.

## 5. Primeros pasos

Al entrar por primera vez puedes abrir **Arctiva Center** (está en el menú de inicio). Sus páginas:

- **Personalización:** modo claro u oscuro, color, fondo, barra de tareas (centrada o a la izquierda, flotante) y tamaño del texto. «Restaurar el aspecto de Arctiva» lo deja como recién instalado.
- **Actualizaciones:** actualiza con un clic los repositorios de Arch, Flatpak y, si lo has activado, el AUR, mostrando antes las noticias de Arch que necesitan tu atención. Antes de cada actualización se guarda una instantánea. Al final de la página eliges qué más se actualiza junto al sistema.
- **Aplicaciones:** la tienda. Busca programas de los repositorios de Arch y de Flathub; el origen siempre se ve. Si hay actualizaciones pendientes, te pide actualizar antes. Puedes poner varias instalaciones o desinstalaciones en cola y se ejecutan una a una.
- **Controladores:** detecta tu gráfica e instala lo necesario (NVIDIA incluida).
- **Extras:** Juegos (Steam, Lutris…), Oficina (LibreOffice, Thunderbird), kernel LTS, Programas de Windows (Bottles), Heroic y ProtonPlus.

## 6. Volver atrás si algo falla (instantáneas)

Antes y después de cada instalación o actualización, Arctiva guarda una **instantánea** del sistema (Btrfs). Si algo deja de funcionar:

1. Reinicia y, en el menú de arranque, elige **«Arctiva snapshots»**.
2. Escoge una instantánea anterior al problema. El sistema arranca tal como estaba; los cambios que hagas ahí son temporales.
3. Se conservan como máximo 10.

## 7. Juegos

Instala el extra **Juegos** (Steam con Proton, Lutris, GameMode, MangoHud, Gamescope). **Heroic** es para tus juegos de Epic, GOG y Amazon, y **ProtonPlus** gestiona las versiones de Proton. Los juegos con anti-trampas a nivel de kernel suelen no funcionar en Linux: mira [Are We Anti-Cheat Yet?](https://areweanticheatyet.com/) y [ProtonDB](https://www.protondb.com/).

El extra opcional **Arctiva Games** (Arctiva Center → Extras, unos 0,5 GB con Wine y winetricks) instala una aplicación aparte, **Arctiva Games**, que abres desde el menú de aplicaciones. Instala lanzadores (Battle.net, EA app, Ubisoft Connect, GOG Galaxy, Epic Games) o cualquier instalador de lutris.net. Antes de instalar muestra qué se descargará y se ejecutará, con el autor del instalador; durante la instalación ves cada paso y el registro en directo, y puedes reintentar, saltar o parar en cualquier paso. En los lanzadores donde hay que iniciar sesión (Battle.net, por ejemplo), el lanzador sigue abierto hasta que pulses **Continuar**. En la live solo se puede explorar. Antes de instalar puedes elegir el ejecutor (Proton o el `wine` del sistema) y si quieres un acceso directo en el menú de aplicaciones o en el escritorio. Los juegos están en `~/Games/<nombre>/` y los registros en `~/.local/share/arctiva-games/logs/`. Los instaladores de lutris.net los escribe su comunidad: revisa antes el resumen.

## 8. Programas de Windows

Instala el extra **Programas de Windows** (Bottles). La primera vez descarga mucho, porque Flatpak también trae sus componentes comunes: Arctiva Center te avisa antes y muestra una barra de progreso, y la descarga puede tardar de unos minutos a más de media hora; no apagues ni suspendas el equipo mientras tanto. Después, haz doble clic en un `.exe` o `.msi` y Arctiva te explica qué va a pasar y lo abre con Bottles. No todo funciona (consulta [WineHQ AppDB](https://appdb.winehq.org/)). Abre solo programas en los que confíes.

## 9. La tienda y el AUR

En **Aplicaciones** puedes instalar y quitar programas de Arch y de Flathub. El **AUR** (recetas de la comunidad sin revisar) está **desactivado**; si lo activas, antes de cada instalación debes leer el PKGBUILD. Si el AUR está activado, sus actualizaciones se hacen junto con las del sistema desde **Actualizaciones**: antes de empezar se muestra qué ha cambiado en cada paquete y no se compila nada hasta que lo apruebas (puedes dejarlo fuera en «Qué se actualiza»).

Puedes pedir varias instalaciones o desinstalaciones seguidas desde la ficha de cada aplicación; se ejecutan una a una. La barra inferior del Center muestra el elemento en curso y su progreso, y **Detalles** abre la lista de elementos y sus registros. Puedes cancelar los que aún no han empezado, limpiar los terminados y cerrar la barra cuando no quede trabajo. El progreso se conserva al salir de una ficha, y no puedes cerrar la ventana del Center mientras haya trabajo pendiente.

## 10. Preguntas frecuentes

- **¿Sigue siendo Arch?** Sí: usa los repositorios oficiales de Arch sin cambios; pacman funciona como siempre.
- **¿Funciona con Secure Boot?** No, desactívalo.
- **¿Y en un equipo con BIOS antigua?** No: solo UEFI.
- **¿Dónde pido ayuda?** En las *Discussions* del repositorio de Arctiva (no en los foros de Arch: no dan soporte a derivadas).
