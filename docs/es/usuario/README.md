# Guía de usuario de Arctiva

> English version: [../../en/user/README.md](../../en/user/README.md)

Arctiva es una distribución Linux basada en Arch Linux, con el escritorio KDE Plasma al estilo de Windows. Esta guía es para quien nunca ha instalado Linux.

**Estado:** versión de pruebas. Aún no hay una ISO pública para descargar; cuando la haya, estará en la página de *Releases* del repositorio, con su suma y su firma (ver [publicación](../publicacion.md)).

## 1. Qué necesitas

- Un equipo con **UEFI** (casi todos los de los últimos 10 años; Arctiva no arranca en modo BIOS antiguo).
- **4 GiB de RAM** como mínimo y **25 GiB libres** de disco.
- Un USB de 4 GB o más (se borra por completo).
- Conexión a internet durante la instalación (para lo que no cabe en la ISO, como el kernel LTS o los perfiles Juegos y Oficina). Sin conexión se instala igual lo que trae la ISO.

## 2. Preparar el USB

Descarga la ISO y comprueba que es auténtica (ver [publicación](../publicacion.md)). Después, con uno de estos programas:

- **Rufus** (Windows): elige la ISO, el esquema de partición **GPT** y el sistema de destino **UEFI**.
- **balenaEtcher** (Windows, macOS, Linux): elige la ISO y el USB.
- **Ventoy** (Windows, Linux): copia la ISO al USB ya preparado con Ventoy.
- **dd** (Linux): `sudo dd if=arctiva-X.Y.Z-x86_64.iso of=/dev/sdX bs=4M status=progress oflag=sync` (cuidado: `/dev/sdX` es el USB, no tu disco).

## 3. Antes de arrancar: Secure Boot y BitLocker

- **Secure Boot** (D-05): Arctiva **no** arranca con Secure Boot activado. Entra en la configuración del firmware (UEFI/BIOS; suele ser Supr, F2 o F12 al encender) y desactívalo.
- **BitLocker (Windows):** si vas a instalar **junto a Windows** y Windows usa BitLocker (o «cifrado del dispositivo»), **ten a mano la clave de recuperación** de tu cuenta Microsoft: Windows la pedirá al cambiar la configuración de arranque. Reduce la partición de Windows desde la *Administración de discos* de Windows y apaga Windows del todo (el *inicio rápido* deja el disco en un estado que impide redimensionarlo).
- Haz **copia de seguridad** de lo importante. Instalar siempre tiene algún riesgo.

## 4. Arrancar e instalar

1. Arranca desde el USB (menú de arranque del firmware, suele ser F12 o F8) y elige «Arctiva (live)». Si la pantalla sale mal, prueba «safe graphics».
2. Pruébalo sin instalar: es una sesión en vivo completa. Cuando quieras, abre **Instalar Arctiva**.
3. Sigue el instalador: idioma, zona horaria y teclado; el **perfil** (Básico, Juegos u Oficina; con Ctrl+clic eliges varios); la página **Comprobación**, que avisa de Windows hibernado, BitLocker, batería y red; el **disco** (borrar todo, **instalar junto a otro sistema** o reemplazar una partición); y tu usuario y contraseña.
4. En la página del disco, **cifrar el sistema** es opcional. Si lo activas, al arrancar GRUB te pedirá la contraseña **en modo texto** antes de mostrar nada más: es normal.
5. Revisa el **resumen** y pulsa Instalar. Al terminar, reinicia y quita el USB.

## 5. Primeros pasos

Al entrar por primera vez puedes abrir **Arctiva Center** (está en el menú de inicio). Sus páginas:

- **Personalización:** modo claro u oscuro, color, fondo, barra de tareas (centrada o a la izquierda, flotante) y tamaño del texto. «Restaurar el aspecto de Arctiva» lo deja como recién instalado.
- **Actualizaciones:** actualiza el sistema con un clic, mostrando antes las noticias de Arch que necesitan tu atención. Antes de cada actualización se guarda una instantánea.
- **Aplicaciones:** la tienda. Busca programas de los repositorios de Arch y de Flathub; el origen siempre se ve. Si hay actualizaciones pendientes, te pide actualizar antes.
- **Controladores:** detecta tu gráfica e instala lo necesario (NVIDIA incluida).
- **Extras:** Juegos (Steam, Lutris…), Oficina (LibreOffice, Thunderbird), kernel LTS, Programas de Windows (Bottles), Heroic y ProtonPlus.

## 6. Volver atrás si algo falla (instantáneas)

Antes y después de cada instalación o actualización, Arctiva guarda una **instantánea** del sistema (Btrfs). Si algo deja de funcionar:

1. Reinicia y, en el menú de arranque, elige **«Arctiva snapshots»**.
2. Escoge una instantánea anterior al problema. El sistema arranca tal como estaba; los cambios que hagas ahí son temporales.
3. Se conservan como máximo 10.

## 7. Juegos

Instala el extra **Juegos** (Steam con Proton, Lutris, GameMode, MangoHud, Gamescope). **Heroic** es para tus juegos de Epic, GOG y Amazon, y **ProtonPlus** gestiona las versiones de Proton. Los juegos con anti-trampas a nivel de kernel suelen no funcionar en Linux: mira [Are We Anti-Cheat Yet?](https://areweanticheatyet.com/) y [ProtonDB](https://www.protondb.com/).

## 8. Programas de Windows

Instala el extra **Programas de Windows** (Bottles). Después, haz doble clic en un `.exe` o `.msi` y Arctiva te explica qué va a pasar y lo abre con Bottles. No todo funciona (consulta [WineHQ AppDB](https://appdb.winehq.org/)). Abre solo programas en los que confíes.

## 9. La tienda y el AUR

En **Aplicaciones** puedes instalar y quitar programas de Arch y de Flathub. El **AUR** (recetas de la comunidad sin revisar) está **desactivado**; si lo activas, antes de cada instalación debes leer el PKGBUILD. Las actualizaciones del AUR son manuales y muestran qué ha cambiado.

## 10. Preguntas frecuentes

- **¿Sigue siendo Arch?** Sí: usa los repositorios oficiales de Arch sin cambios; pacman funciona como siempre.
- **¿Funciona con Secure Boot?** No, desactívalo.
- **¿Y en un equipo con BIOS antigua?** No: solo UEFI.
- **¿Dónde pido ayuda?** En las *Discussions* del repositorio de Arctiva (no en los foros de Arch: no dan soporte a derivadas).
