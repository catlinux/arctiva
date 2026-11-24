# Pendiente

> English version: [TODO.md](TODO.md)

Trabajo pendiente agrupado por prioridad. Fases y decisiones: [hoja de ruta](docs/es/hoja-de-ruta.md) · [arquitectura](docs/es/arquitectura.md).

## Media: fase 2 (instalador)

- [ ] ISO live con GRUB en lugar de systemd-boot (`bootmodes=('uefi.grub')`, `iso/grub/` con el tema de Arctiva, quitar `iso/efiboot/`): hace falta una máquina Arch para probar `mkarchiso`; `tests/boot-test.sh` no cambia (arranca el kernel directamente).

- [ ] Al arrancar una instantánea falla `systemd-remount-fs` (fstab pide `subvol=/@` y la raíz es un overlay de grub-btrfs). No impide arrancar; valorar ocultarlo.
- [ ] Las páginas QML del instalador llevan sus textos en castellano, catalán e inglés dentro del propio QML; pasarlos a traducciones del branding (`.ts`) para poder añadir más idiomas.
- [ ] Mapa sin conexión en la página «Idioma y zona»: el de Calamares descarga los mosaicos de Internet, así que de momento la página usa solo listas.
- [ ] La lista de perfiles necesita Ctrl+clic para elegir varios (Calamares usa selección extendida; la pista va en el texto de «Básico»). Una página QML propia permitiría el clic simple.
- [ ] Volver a probar «Instalar junto a» con el nuevo requisito de 25 GiB (0.3.13) en un disco de 60 GB con Windows.
- [ ] ISO más ligera, siguiente paso: las aplicaciones opcionales de KDE ya están diferidas (ver `deferred-packages`). Lo que queda es sobre todo firmware (`linux-firmware-*` ~430 MiB: Intel 142, NVIDIA 104, Atheros 53, MediaTek 37, AMDGPU 28; el de la gráfica y el Wi-Fi no se puede diferir porque el primer arranque y la primera conexión lo necesitan) y `firefox` (307 MiB, se queda: los portales cautivos necesitan un navegador). Medido el 2026-11-23: ISO de 1,92 GB, 830 paquetes, 4,68 GiB sin comprimir.

## Media: instalador

- [ ] Ventoy en modo normal falla en el PC de sobremesa (en el portátil funciona): revisar Secure Boot y el modo de arranque de esa placa.
- [ ] Ventoy en modo normal se queda en un shell de emergencia (solo arranca el «modo grub2»): probablemente Ventoy reconoce archiso por `/arch/` y Arctiva usa `install_dir="arctiva"`. Comprobarlo en QEMU con un disco de Ventoy; si se confirma, valorar cambiar `install_dir` a `arch` (afecta a `unpackfs`, al instalador y a los scripts).
- [ ] Arranque lento de la live desde un USB: 1 min 53 s en un portátil con Ventoy (loader 32 s, kernel 49 s porque archiso copia el sistema de 1,7 GiB a la RAM, espacio de usuario 25 s). Valorar `copytoram=n` (arranca antes, programas más lentos) o un mensaje de progreso.
- [ ] En la página «Perfiles» del instalador, la imagen del perfil toca el borde derecho de la ventana.

## Media: estudios

- [ ] Comprobaciones del instalador en la VM, antes de la fase 2 (D-03, D-04): qué hacen y qué necesitan `localeq`, `packagechooserq` y `notesqml` de Calamares 3.4.3; `os-prober` con Windows, BitLocker e inicio rápido; alcance de `stylesheet.qss` en la página de disco.

## Más adelante

- Arctiva Games, elegir el script de instalación de cada lanzador (receta de Arctiva, script de Lutris u otros de otras distribuciones que funcionen): diseñarlo antes, porque ejecuta código descargado de terceros.
- Arctiva Games (paquete opcional `arctiva-games` y extra, 0.1.0, programado pero **sin probar en hardware real**): hacer una instalación completa de Battle.net en una VM con aceleración o en hardware real y comprobar que el lanzador queda abierto hasta pulsar Continuar; diagnosticar el caso del servidor privado de WoW con `lutris -d` (paso 1 del plan); ajustar el orden de ejecutores Proton por lanzador en hardware real (Battle.net con el `wine` del sistema se cae en su motor de navegador); implementar `extract`, `move`, `merge`, `input_menu` y archivos que aporta el usuario; escribir al equipo de Lutris antes de publicar; prueba manual con scripts populares de lutris.net (paso 9 del plan). Detalles en el plan de juegos.
- Instalar desde dentro de Windows (asistente que descarga la ISO, la verifica y graba el USB): aparcado por el mantenedor, no planificado.
- Fases 2 a 7 según la hoja de ruta.
- Pruebas en hardware real (USB en el PC con la RTX 4060; portátil con Windows y Manjaro), solo al final, con todo implementado (fase 7). La entrada «safe graphics» ya funciona en VirtualBox.
- Hibernación: subvolumen `@swap` con un archivo de intercambio además de zram (D-04). Queda fuera de la 1.0, que solo tiene suspensión.
- ISO reproducible bit a bit: dos construcciones con la misma fecha del Arch Linux Archive tienen los mismos paquetes y tamaño, pero distinta suma (D-02).
- Cifrado LUKS2 con desbloqueo por TPM2 o FIDO2, cuando Calamares permita elegir el método de derivación de la clave (D-04).
- Contraseña de cifrado con la distribución de teclado del usuario en GRUB (`grub-kbdcomp`), en lugar de la estadounidense (D-04).

- Compilar los paquetes propios (`packages/`) con la misma fecha del Arch Linux Archive que la ISO: obligaría a bajar de versión el equipo de construcción con `pacman -Syyuu`, algo seguro solo en un contenedor desechable; de momento se compilan con las bibliotecas del día (explicado en `docs/es/desarrollo.md`). Reconsiderar si Calamares deja de arrancar por una biblioteca más nueva que la de la ISO.

## Descartado

- **Evitar que `pam_faillock` bloquee al usuario `live`:** el acceso SSH de la live usa una contraseña aleatoria, así que nadie adivina contraseñas y el bloqueo no llega a darse.
- **Bifurcar o retener paquetes oficiales de Arch:** rompe la compatibilidad con el AUR y multiplica el mantenimiento (D-01).
- **Motor PackageKit de Discover:** mal soporte en Arch y riesgo de actualizaciones parciales (D-07).
- **Discover con un motor propio, Pamac, Bauh u Octopi como tienda:** sin motor para pacman en Discover y sin interfaz estable para escribirlo; los demás dependen del AUR, están parados o no tienen Flatpak (D-07).
- **Instalador escrito desde cero:** el particionado y el redimensionado de Windows es donde se pierden datos; en su lugar se personaliza Calamares (D-03).
- **LUKS2 con Argon2id o `/boot` sin cifrar en la 1.0:** con Argon2id hay informes de GRUB sin memoria al arrancar, y un `/boot` aparte rompe las instantáneas arrancables (D-04).
- **BIOS heredada en la 1.0:** duplica la matriz de pruebas con muy poco beneficio (D-04).
- **Partir la ISO en trozos:** las herramientas para grabar USB necesitan un único archivo (D-14).
- **Paquete nativo de Bottles:** sus desarrolladores solo soportan Flatpak (D-12).
- **Aviso en el resumen si la raíz no es Btrfs:** Calamares no deja la tabla de particiones en GlobalStorage hasta que se ejecuta la instalación, así que una página QML no puede saberlo; la guía de usuario explica que las instantáneas necesitan una raíz Btrfs.
