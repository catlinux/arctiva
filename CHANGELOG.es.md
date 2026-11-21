# Registro de cambios

Todos los cambios relevantes del proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/).

> English version: [CHANGELOG.md](CHANGELOG.md)

## [Sin publicar]

## [0.5.0] - 2026-11-21

Fase 4 terminada: Arctiva Center (bienvenida, actualizaciones, controladores y extras). Pruebas de cierre superadas el 2026-11-21: actualización desde Arctiva Center, un extra, controladores con un `lspci` simulado, `.pacnew`, el hook de GRUB con LUKS y una instalación nueva cifrada con la ISO 0.4.1 que arranca la entrada por defecto y la instantánea inicial. Sin cambios de código. Versión menor (fase terminada, D-16).

## [0.4.1] - 2026-11-21

Corrección del arranque tras instalar, encontrada en las pruebas de cierre de la fase 4. Versión de parche.

### Corregido

- El sistema instalado podía no arrancar la entrada por defecto de GRUB (`error: premature end of file /@/boot/vmlinuz-linux`, y después `you need to load the kernel first`): la copia del sistema con `rsync -S` dejaba la cola de ceros del kernel como un hueco en Btrfs, y GRUB lo leía como el final del archivo. El kernel se copia ahora sin huecos, también en `/usr/lib/modules`, de donde lo vuelve a copiar mkinitcpio al actualizarse. Se vio en una instalación cifrada, pero podía pasar también sin cifrado. El kernel LTS no estaba afectado.
- Arctiva Center 0.6.2: el registro de pacman en Actualizaciones, Extras y Controladores, y el diff de los `.pacnew`, se cortaban a la altura del recuadro y no se podían desplazar. Ahora tienen barra de desplazamiento y el registro baja solo hasta la última línea mientras corre.

### Cambiado

- Hoja de ruta: la identidad y un escritorio sencillo parecido a Windows pasan a ser la fase 5 (0.6.0), antes que la tienda, que pasa a la fase 6 (0.7.0). La fase 5 suma un módulo «Personalización» en Arctiva Center con los ajustes básicos y «Restaurar el aspecto de Arctiva», el menú de GRUB siempre visible con tema propio y límites para las instantáneas. Las pruebas de Steam, Proton y Heroic en hardware real pasan a la fase 7.
- `build.sh` admite espejos extra del Arch Linux Archive para la misma fecha fijada (variable `ARCHIVE_MIRRORS`, sin mezclar nunca con mirrors actuales) y comprueba con reintentos que alguno responde antes de construir, fallando pronto con un mensaje claro.

## [0.4.0] - 2026-11-21

Fase 3 cerrada: el sistema instalado usa el repositorio firmado `[arctiva]`. Probado con una instalación completa de la ISO 0.3.17 en QEMU (UEFI, con red y el perfil Juegos): `pacman -Sy` descarga y valida `arctiva.db`, los cinco paquetes propios vienen de `[arctiva]`, la clave de firma tiene confianza total, y `os-release`, zram, `reflector.timer`, multilib, los paquetes de Juegos, el kernel LTS en GRUB y la instantánea inicial están en su sitio. El instalador ejecuta `/usr/lib/arctiva/install-drivers`. En reposo, tras iniciar sesión, el sistema usa unos 1,2 GB de RAM. Versión menor (fase terminada, D-16).

### Corregido

- En el panel del sistema instalado quedaba un icono en blanco: el lanzador de Discover, que el instalador quita. Un script de actualización de Plasma lo cambia por Arctiva Center la primera vez que el usuario inicia sesión; en la ISO live, con Discover, no hace nada (`arctiva-center` 0.6.1).

## [0.3.17] - 2026-11-21

GRUB al día tras las actualizaciones (fase 4, paso 4.7). Versión de parche.

### Añadido

- `arctiva-settings` 0.2.0: hook de pacman `arctiva-grub.hook` y `/usr/lib/arctiva/update-grub`. Al actualizar el paquete `grub` se reinstala GRUB en la partición EFI (`EFI/arctiva`) y se regenera `grub.cfg`. La copia de reserva `EFI/Boot/BOOTX64.EFI` solo se actualiza si es la de Arctiva (otra, como la de Windows, no se toca). Si `grub-install` falla, `grub.cfg` no se regenera y un mensaje claro pide no reiniciar. No hace nada en equipos BIOS, sin la partición EFI montada o sin `EFI/arctiva`.
- `tests/update-grub-test.sh` (8 casos).

## [0.3.16] - 2026-11-21

Bienvenida de Arctiva Center (fase 4, paso 4.6). Versión de parche.

### Añadido

- Página de bienvenida: logo y versión, el estado de los controladores gráficos, las actualizaciones y los extras con un botón a cada módulo, y cómo volver a una instantánea desde el menú de GRUB. Se abre al iniciar sesión (`/etc/xdg/autostart/arctiva-center-welcome.desktop`) hasta que se desmarca «Mostrar esta bienvenida al iniciar sesión»; en la ISO live nunca se abre sola.
- En la ISO live, Arctiva Center muestra un aviso y desactiva sus acciones de instalar y actualizar.
- `arctiva-center` 0.6.0.

## [0.3.15] - 2026-11-21

Módulo «Extras» de Arctiva Center (fase 4, paso 4.5). Versión de parche.

### Añadido

- Módulo Extras: Juegos, Oficina y Kernel LTS, cada uno con un interruptor para instalarlo o quitarlo. Juegos y Oficina tienen los mismos paquetes que los perfiles del instalador (una prueba falla si divergen). El kernel LTS instala también el módulo de NVIDIA que corresponda y actualiza el menú de GRUB al instalarlo y al quitarlo. La impresión y el cortafuegos ya vienen en el sistema base: el módulo enlaza a sus páginas de Configuración del sistema.
- Ayudante: al quitar un extra se conservan los paquetes que siga usando otro extra instalado (por ejemplo, las tipografías que comparten Juegos y Oficina); `remove_also` y `update_grub` en el catálogo.
- `arctiva-center` 0.5.0.

### Corregido

- Ayudante: quitar un extra fallaba porque la simulación usaba `pacman -Rns --print`, una combinación que pacman rechaza; ahora usa `-Rs --print`.

## [0.3.14] - 2026-11-21

Módulo «Controladores» de Arctiva Center (fase 4, paso 4.4). Versión de parche.

### Añadido

- Módulo Controladores: tarjetas gráficas detectadas, los controladores que necesitan y si están instalados, con un botón «Instalar controladores» (operación `drivers-apply` del ayudante); para las NVIDIA antiguas (GTX 10/900 y anteriores), una explicación de por qué se usa el controlador libre nouveau y qué supone la opción del AUR.
- `tests/install-drivers-test.sh`: `install-drivers --upgrade` con `pacman`, `systemctl` y `mkinitcpio` falsos.
- `arctiva-hardware` 0.2.0 y `arctiva-center` 0.4.0.

### Cambiado

- `install-drivers` pasa del instalador a `arctiva-hardware` (`/usr/lib/arctiva/install-drivers`), compartido por el instalador y Arctiva Center. Nuevo modo `--upgrade` para el sistema en marcha: `pacman -Syu --needed`, servicios activados en el momento, `mkinitcpio -P` al final y código de error si algo falla (arquitectura, D-10).

## [0.3.13] - 2026-11-21

Requisitos más bajos. Versión de parche.

### Cambiado

- Disco: 25 GB como mínimo (40 GB recomendados); el instalador pide ahora 25 GiB, lo que además permite «Instalar junto a» en discos más pequeños. El sistema base ocupa unos 5 GB.
- Medio de instalación: basta un USB de 4 GB (la ISO ocupa 1,76 GiB).
- La RAM sigue en 4 GB (8 GB recomendados) hasta medirla en un sistema instalado.

## [0.3.12] - 2026-11-21

Módulo «Actualizaciones» de Arctiva Center (fase 4, paso 4.3). Versión de parche.

### Añadido

- Módulo Actualizaciones: lista de `checkupdates` con los paquetes delicados marcados (`delicate.toml`); noticias de Arch Linux publicadas desde la última actualización completa terminada, donde una noticia que exige intervención manual bloquea la actualización hasta marcarla como leída; actualización con el registro real; explicación traducida de los errores habituales de pacman (`errors.toml`: base bloqueada, sin espacio, firmas PGP, archivos en conflicto, dependencias rotas, red) con la acción «Actualizar primero el anillo de claves» o «Volver a intentarlo»; actualización de Flatpak después; archivos `.pacnew` pendientes con su diferencia y «Quedarme el mío» / «Usar el nuevo»; reinicio recomendado si cambió el kernel, NVIDIA, Mesa, systemd o glibc.
- Aviso de actualizaciones: temporizador de usuario `arctiva-center-check.timer` (a los 15 minutos de iniciar sesión y después cada 6 horas) que ejecuta `arctiva-center --check` y muestra una notificación con un botón que abre el módulo, solo si hay actualizaciones que no estaban en el aviso anterior. No funciona en la ISO live.
- `arctiva-center` 0.3.0.

### Cambiado

- El ayudante ejecuta pacman con los mensajes en inglés para reconocer los errores en cualquier idioma (arquitectura, D-08).

## [0.3.11] - 2026-11-21

Ayudante privilegiado de Arctiva Center (fase 4, paso 4.2). Versión de parche.

### Añadido

- `arctiva-helper`, lanzado con `pkexec` y la acción polkit `org.arctiva.center.helper` (`auth_admin_keep`, solo sesiones activas). Acepta un conjunto cerrado de operaciones (`update`, `extra-install`, `extra-remove`, `drivers-apply`, `pacnew-keep`, `pacnew-use`) y nunca nombres de paquetes ni órdenes: los paquetes y servicios salen de su propio catálogo, las rutas `.pacnew` deben ser archivos normales dentro de `/etc` sin enlaces, y cualquier otra cosa sale con el código 64 sin ejecutar nada. No actúa mientras la base de pacman está bloqueada.
- Arctiva Center lanza el ayudante sin shell y muestra su salida línea a línea; la ventana no se puede cerrar mientras trabaja. La página Actualizaciones tiene un botón provisional «Actualizar el sistema».
- Pruebas del ayudante con `pacman` y `systemctl` falsos, incluidas rutas trampa e identificadores no válidos.
- `arctiva-center` 0.2.0.

### Cambiado

- El repositorio ya es público; arquitectura (D-01) y hoja de ruta actualizadas.

## [0.3.10] - 2026-11-21

Versión de parche: solo documentación.

### Cambiado

- Hoja de ruta: repositorio `[arctiva]` firmado marcado como hecho. La primera publicación (cinco paquetes) y la comprobación desde un sistema limpio con `SigLevel = Required` pasaron en el CI.

## [0.3.9] - 2026-11-21

### Corregido

- Comprobación del repositorio: la firma del anillo se guarda con otro nombre para que `pacman -U` no exija una clave que aún no está en el anillo.

## [0.3.8] - 2026-11-21

### Corregido

- Publicación del repositorio: se copia el logo que necesita `arctiva-branding` al directorio de compilación, la base se copia sobre los enlaces que deja `repo-add` y se quita un argumento sobrante de la orden de subida. Script probado entero en un contenedor `archlinux` con una clave desechable.

## [0.3.7] - 2026-11-21

### Corregido

- Publicación del repositorio: el usuario de compilación no podía entrar en el directorio de trabajo temporal (creado con permisos 700) y no se compilaba ningún paquete.

## [0.3.6] - 2026-11-21

Repositorio `[arctiva]` firmado (fase 3, pasos 3.3 y 3.4). Versión de parche: no se publica nada hasta el primer push.

### Añadido

- Paquete `arctiva-keyring` con la clave pública del repositorio, de confianza total, en la ISO y en el sistema instalado.
- Flujo `Repositorio` y `packages/publish-repo.sh`: compilan, firman y publican los paquetes `arctiva-*` en `catlinux/arctiva-repo` y comprueban que un sistema limpio puede instalar desde él con `SigLevel = Required`.
- El sistema instalado recibe la sección `[arctiva]` al final de la instalación, con su servidor en `/etc/pacman.d/arctiva-mirrorlist` (`arctiva-settings` 0.1.1).

## [0.3.5] - 2026-11-21

Esqueleto de Arctiva Center (fase 4, paso 4.1). Versión de parche: paquete nuevo sin funcionalidad todavía.

### Añadido

- `center/`: ventana de Arctiva Center (PySide6, QML y Kirigami) con barra lateral Bienvenida, Actualizaciones, Controladores y Extras, lanzador (`--welcome`, `--check`, `--module`), traducciones al castellano y al catalán, catálogos de datos mínimos y pruebas con `pytest`.
- Paquete `arctiva-center`, publicado en `[arctiva]` e incluido en la ISO; `center/**` activa los flujos del repositorio y de la ISO.

## [0.3.4] - 2026-11-21

Comprobaciones previas de Arctiva Center en la ISO live. Versión de parche: solo documentación.

### Cambiado

- Arquitectura (D-08): arch-update evaluado y descartado como dependencia (solo en el AUR, herramienta de terminal y bandeja); se usan directamente `checkupdates`, el RSS y `pacdiff`. `arctiva-center` dependerá de `fakeroot`, que `checkupdates` necesita y `pacman-contrib` no declara.
- Hoja de ruta: evaluación de arch-update marcada como hecha.

## [0.3.3] - 2026-11-21

Diseño de Arctiva Center y cambios en la hoja de ruta. Versión de parche: solo documentación.

### Cambiado

- Arquitectura (D-09): diseño de Arctiva Center para la fase 4 (interfaz en QML y Kirigami, ayudante con `pkexec` y un conjunto cerrado de operaciones, temporizador de aviso de actualizaciones, hook de GRUB).
- Hoja de ruta: la fase 4 añade reinstalar GRUB en la partición EFI al actualizar el paquete `grub`; la fase 6, un tema gráfico de GRUB.

## [0.3.2] - 2026-11-21

Detección de gráficas e instalación de controladores (D-10). Versión de parche, según la política de versiones de los pasos de la fase 3.

### Añadido

- Paquete `arctiva-hardware` con `arctiva-gpu`, que lee `lspci -nn` y decide los controladores: NVIDIA Turing o posterior (id PCI `>= 0x1E00`) recibe `nvidia-open` y `nvidia-utils` (más `nvidia-open-lts` con el kernel LTS y `lib32-nvidia-utils` con Steam); la NVIDIA anterior sigue con `nouveau` y un aviso; AMD e Intel no necesitan nada extra; con dos o más GPU reales se activa `switcheroo-control`.
- Paso del instalador que instala esos controladores tras los paquetes y antes de generar el initramfs, con KMS temprano de NVIDIA. Sin conexión, o si algo falla, la instalación sigue con el controlador libre.
- Página «Comprobación del equipo»: avisos para NVIDIA moderna (necesita conexión) y NVIDIA antigua (usa `nouveau`).
- `tests/gpu-detect-test.sh` con muestras de `lspci`.

## [0.3.1] - 2026-11-21

Fase 3, primer paso: los paquetes de identidad del sistema instalado. Versión de parche: no añade comportamiento al instalador.

### Añadido

- Paquete `arctiva-settings`: configuración de zram (movida desde la ISO), un hook de pacman que reescribe `/usr/lib/os-release` para que el sistema se identifique como Arctiva tras cada actualización de `filesystem`, y la configuración de `reflector`. El sistema instalado activa `reflector.timer`.
- Paquete `arctiva-branding`: el logo de la distribución y la configuración de «Acerca de este sistema» de Plasma.
- Guía de las claves de firma del repositorio ([docs/es/firma.md](docs/es/firma.md)).

### Cambiado

- D-01: `[arctiva]` solo contiene lo que usa el sistema instalado; `calamares`, `ckbcomp` y la configuración del instalador siguen solo en la ISO. D-10: la regla de NVIDIA es el id de dispositivo PCI (`>= 0x1E00`).

## [0.3.0] - 2026-11-21

Fase 2 cerrada: el instalador está completo y probado en máquinas virtuales (UEFI, QEMU/KVM). Probado: borrar disco, con y sin cifrado; particionado manual (ESP propia y raíz Btrfs); «Instalar junto a» un Windows simulado (NTFS reducido, ESP reutilizada, `os-prober` añade Windows a GRUB); perfiles con y sin conexión. Las pruebas con Windows y hardware reales quedan para la fase 7.

### Añadido

- Guía de desarrollo: cómo probar la instalación junto a otro sistema y el particionado manual, y el tamaño de disco que necesitan.

## [0.2.8] - 2026-11-21

Fase 2, perfiles (segunda parte): aspecto, resumen y tamaños. Pendiente de la aprobación del usuario con capturas.

### Añadido

- Página de perfiles con la paleta del instalador (tarjetas, elemento seleccionado con borde y fondo) y una imagen por perfil (`perfil-juegos.svg`, `perfil-oficina.svg`, `perfil-basico.svg`).
- Elemento «Básico» en la lista, que explica que se instala siempre y cómo añadir los demás (mantener Ctrl y hacer clic: la lista usa selección extendida).
- Tarjeta «Perfiles» en el resumen con lo elegido, deducida de las operaciones de paquetes que deja la página.

### Corregido

- `tests/fake-windows-disk.sh` crea también `EFI/Microsoft/Boot/BCD`: sin él `os-prober` no reconoce el Windows simulado y GRUB no recibe entrada para él.

### Cambiado

- Las descripciones de Juegos y Oficina incluyen el tamaño de descarga (unos 0,3 GB cada uno, medido con `pacman -Sp` sobre la base de la ISO).

## [0.2.7] - 2026-11-20

Fase 2, perfiles (primera parte): configuración y multilib. El aspecto, el resumen y los tamaños de descarga siguen en la 0.2.8.

### Añadido

- Página «Perfiles» del instalador (`packagechooser` de widgets, con varias opciones) con Juegos y Oficina. Básico es lo que ya lleva la ISO y se instala siempre. Los paquetes se instalan desde los repositorios si hay conexión; sin ella, solo se instala Básico.

### Cambiado

- `multilib` queda activo en el sistema instalado.

### Cambiado

- Fase 2, paso 4 cerrado: el usuario aprueba con capturas la interfaz del instalador (barra lateral, navegación, páginas QML propias y presentación de la 0.2.4–0.2.6).

## [0.2.6] - 2026-11-20

Fase 2, paso 4 (segunda parte): páginas QML propias del instalador. Pendiente de la aprobación del usuario con capturas. Los perfiles se aplazan: `packagechooserq` solo admite una opción.

### Añadido

- Páginas QML de Arctiva para la bienvenida, idioma y zona, teclado, cuenta, resumen y fin, con los colores de las maquetas y textos en castellano, catalán e inglés. La de idioma y zona funciona sin conexión (listas en lugar del mapa de Calamares, que descarga los mosaicos de Internet). La del teclado busca distribuciones y tiene un campo de prueba; la de la cuenta indica la fuerza de la contraseña.
- Presentación propia durante la instalación: instantáneas, Plasma, Arch al día y cifrado.
- `build.sh -c <dir>`: repositorio local que se conserva entre construcciones; solo se recompila lo que cambia de versión (la configuración del instalador, siempre). Evita compilar Calamares en cada ISO.

### Cambiado

- El instalador usa los módulos QML de Calamares (`welcomeq`, `localeq`, `keyboardq`, `usersq`, `summaryq`, `finishedq`) en lugar de los de widgets, salvo el de disco.

## [0.2.5] - 2026-11-20

Corrección del instalador (parche). Probado en QEMU con la ISO 0.2.5: el sistema instalado arranca sin Discover ni Calamares; también se comprobaron los dos cambios de 0.2.4 que faltaban (BitLocker detectado con `blkid -p` y nombres de los pasos traducidos).

### Corregido

- Discover seguía en el sistema instalado y mostraba «Problema de actualización» al abrirlo: la preparación del destino lo quita junto a Calamares (D-07; en la live se queda).

### Cambiado

- Las pruebas en hardware real (PC con NVIDIA y portátil con Windows y Manjaro) pasan a la fase 7: se harán al final, con todo implementado. La fase 2 se cierra con pruebas en máquinas virtuales.

## [0.2.4] - 2026-11-20

Fase 2, paso 4 (primera parte): identidad del instalador. Pendiente de la aprobación del usuario con capturas; las páginas QML (`*q`) y la presentación quedan para la segunda parte. Probado también «Instalar junto a» en QEMU (disco de 80 GB, NTFS simulado de 60 GB): Calamares lo reduce con `ntfsresize`, instala y arranca, y el NTFS queda sano; `os-prober` no reconoce el Windows simulado y se comprobará con uno real (paso 2.5).

### Añadido

- Barra lateral y navegación del instalador en QML, según las maquetas: degradado azul noche, símbolo y versión de Arctiva, pasos numerados (el actual en una píldora azul, los hechos con marca), «Siguiente» en azul y «Hecho» como botón principal en la última página.
- `stylesheet.qss` para las páginas de widgets (particionado, usuarios, resumen) con la paleta del logo; el logo y el icono salen de `branding/logo/` al empaquetar.

### Corregido

- La entrada «Install System» de Calamares seguía en el menú de la live junto a «Instalar Arctiva»: ahora la quita la preparación de la live.

## [0.2.3] - 2026-11-20

Fase 2, paso 3: lanzador y página «Comprobación». Probado en QEMU con un disco que simula Windows (los tres niveles); falta la prueba con un Windows 11 real (paso 2.5).

### Añadido

- Lanzador `arctiva-installer` (entrada «Instalar Arctiva» del menú, que sustituye a la de Calamares): revisa el equipo con `detect-system` y abre Calamares. Detecta Windows (`bootmgfw.efi` en una ESP), particiones BitLocker, NTFS hibernado (`ntfs-3g.probe`, código 14), batería sin cargador y conexión a Internet, y lo deja en `/run/arctiva/equipo.json`.
- Página «Comprobación» (`notesqml`) antes de la de disco, en castellano, catalán e inglés según el idioma elegido: bloqueo (Windows hibernado o con inicio rápido, con botón para salir), aviso (BitLocker, batería) o correcto, más avisos de la hora de Windows y de la falta de red.
- `tests/fake-windows-disk.sh`: simula en la VM un disco con Windows limpio, hibernado o con BitLocker.
- `ntfsprogs` en la ISO: `ntfsresize`, que KPMcore necesita para reducir Windows, ya no viene en `ntfs-3g`.

### Cambiado

- D-03: el nivel de bloqueo es una recomendación (Calamares no deja desactivar «Siguiente» desde QML); lo que impide instalar junto a un Windows hibernado es `ntfsresize`.

## [0.2.2] - 2026-11-20

Fase 2, paso 2: configuración base del instalador (sin interfaz propia). Probado en QEMU con UEFI: instalación borrando el disco, sin cifrar y cifrada, arranque del sistema instalado, `snapper list` y arranque de la instantánea inicial desde GRUB (también con la raíz cifrada; GRUB desbloquea en unos 5 s).

### Añadido

- Paquete `arctiva-calamares-config` en `installer/` (va a `/etc/calamares/` de la ISO live y se quita del sistema instalado): secuencia de páginas con los módulos de widgets, Btrfs con `@`, `@home`, `@cache`, `@log` y `@snapshots`, sin swap en disco, cifrado LUKS1 opcional con una sola contraseña en GRUB, GRUB en `EFI/arctiva` con `os-prober`, copia de respaldo `BOOTX64.EFI`, `linux` como entrada por defecto, submenú «Arctiva snapshots» y sin las entradas «EFI BootNext» de GRUB 2.16, hooks clásicos de mkinitcpio con `grub-btrfs-overlayfs`, servicios del sistema y `linux-lts` (con `pacman -Syu` antes) si hay red.
- Scripts del instalador: `prepare-target` (copia el kernel, que mkarchiso deja fuera de `/boot`; quita Calamares y `mkinitcpio-archiso`; inicia el llavero de pacman; usa el DNS de la live durante la instalación) y `finish-target` (deja el `resolv.conf` original, Snapper sobre `@snapshots`, instantánea inicial «Arctiva: estado inicial» y menú de GRUB con ella).
- zram (la mitad de la RAM, como máximo 8 GiB) en la live y en el sistema instalado, e `inotify-tools` para `grub-btrfsd`.

### Cambiado

- `packages/build-packages.sh` compila también `arctiva-calamares-config`, y el CI se lanza con cambios en `installer/`.
- La sesión live ya no bloquea la pantalla por inactividad (se bloqueaba en mitad de la instalación).
- `tests/run-live.sh` arranca siempre primero la ISO cuando se le pasa una, aunque la NVRAM recuerde otro orden.

## [0.2.1] - 2026-11-20

Fase 2, paso 1: paquetes del instalador.

### Añadido

- PKGBUILD de `packages/calamares` (Calamares 3.4.3, Qt6, con la firma de las fuentes verificada contra la clave del mantenedor) y de `packages/ckbcomp` (de console-setup 1.249, suma fijada).
- `packages/build-packages.sh` los compila en un repositorio pacman local `arctiva-local`; `build.sh` lo hace solo, o usa uno ya compilado con la nueva opción `-l`.
- `calamares` forma parte de la ISO live (1,76 GiB).

## [0.2.0] - 2026-11-20

Fase 1 terminada: ISO live mínima.

### Añadido

- Perfil archiso de Arctiva en `iso/`, derivado de `releng` (archiso 92): Plasma con sesión automática del usuario `live`, arranque solo UEFI, compresión xz y la selección de paquetes del sistema. Construida y probada en VirtualBox: llega al escritorio y ocupa 1,75 GiB.
- `build.sh`: construcción reproducible con una fecha del Arch Linux Archive (`iso/archive-date`), suma `sha256`, límite de 1,9 GiB y opción `-k` para conservar el directorio de trabajo.
- Flujo de GitHub Actions `iso.yml` con construcción, prueba de arranque en QEMU con UEFI (`tests/boot-test.sh`) y construcción semanal. El primer run pasa.
- `tests/boot-test.sh` ya no necesita root si está `7z`.
- Plan detallado con casillas de cada fase en la hoja de ruta.
- `tests/run-live.sh`: arranca la ISO en QEMU/KVM con un disco virtual y la muestra en el navegador con noVNC.
- El flujo usa `actions/checkout` y `actions/upload-artifact` v7 (Node.js 24), porque Node.js 20 está obsoleto en los runners.

### Cambiado

- D-04 y D-14: `linux-lts` se instala durante la instalación si hay conexión, en lugar de ir en la ISO, y la ISO no lleva la documentación de los paquetes; así baja de 2,12 a 1,75 GiB. Tamaño medido y desglosado en D-14.

## [0.1.7] - 2026-11-20

### Cambiado

- D-03: diseño del instalador fijado sobre Calamares 3.4.3 (Qt 6): orden de las páginas, páginas QML (incluidas la del perfil con `packagechooserq` y una página «Comprobación»), identidad visual y un lanzador que detecta BitLocker y el inicio rápido de Windows antes de particionar, algo que Calamares no hace.
- D-04: cifrado LUKS1 opcional con `/boot` dentro de `@` y una sola petición de contraseña en GRUB, con aviso de la distribución de teclado estadounidense al arrancar; partición EFI en `/boot/efi`; la ISO arranca solo en UEFI.

### Corregido

- D-04: GRUB admite Argon2 desde la 2.14 (Arch tiene la 2.16); LUKS2 sigue fuera por los problemas de memoria descritos con los parámetros de Argon2id que usa Calamares.

## [0.1.6] - 2026-11-20

### Cambiado

- D-07 aprobada: la tienda será un módulo propio de Arctiva Center. Consulta pacman sobre una copia temporal de las bases de datos, instala con `pacman -Syu --needed`, gestiona Flatpak con libflatpak y `flatpak-kcm`, y muestra el PKGBUILD del AUR y su diff en cada actualización. El sistema instalado no lleva Discover, que queda solo en la ISO live.
- D-09: Arctiva Center incorpora el módulo «Aplicaciones».
- El logo de `branding/logo/` queda aprobado (D-13).

## [0.1.5] - 2026-11-20

### Cambiado

- Decisiones de arquitectura D-01…D-16 aprobadas, salvo D-07 (tienda), que sigue en estudio.
- D-03 y D-05: avisos para el arranque dual con Windows (BitLocker no se puede redimensionar desde el instalador, se pide la clave de recuperación al cambiar Secure Boot, el inicio rápido debe estar desactivado).
- D-04: nuevo subvolumen `@snapshots` para que Snapper pueda volver atrás, las instantáneas de solo lectura arrancan con `grub-btrfs-overlayfs`, sin hibernación en la 1.0 y cifrado LUKS limitado a lo que admite GRUB.
- D-06: solo sesión Wayland, ya que KDE retiró la sesión X11 en Plasma 6.8.
- D-15: espacio en disco del runner de GitHub Actions y desactivación de las tareas programadas tras 60 días sin actividad.

### Corregido

- D-10: el paquete de NVIDIA para el kernel LTS es `nvidia-open-lts`.
- Los requisitos de hardware reflejan la VM de construcción ya preparada.

## [0.1.4] - 2026-11-20

### Cambiado

- La guía de desarrollo documenta la preparación comprobada de la VM de construcción y la construcción de la ISO `releng` oficial, que arranca en una VM de pruebas.
- El repositorio de GitHub y el remoto local usan ya el nombre `arctiva`.

## [0.1.3] - 2026-11-20

### Añadido

- Logo de Arctiva en `branding/logo/`: logotipo completo, símbolo a color, símbolo monocromo e icono de aplicación (SVG).
- Logo en la cabecera de los dos README.

## [0.1.2] - 2026-11-20

### Añadido

- Licencia GPL-3.0-or-later (`LICENSE`), con CatLinux como titular.
- Política del nombre y el logo (`TRADEMARKS.es.md`): la marca no está cubierta por la licencia del código.
- Sección de créditos y licencia en los dos README.

## [0.1.1] - 2026-11-20

### Cambiado

- El proyecto pasa a llamarse Arctiva en lugar de Archtiva, también en los nombres de paquetes, repositorio e ISO.
- D-03: Calamares sigue como motor de instalación, con la interfaz rehecha en QML y una hoja de estilo Qt para que lleve la identidad del proyecto, sin parchear su código.
- D-07: la tienda ofrecerá los repositorios oficiales, Flathub y el AUR como fuentes separadas, con el AUR desactivado por defecto y con avisos; la solución concreta pasa a estudio.
- D-13: identidad actualizada con el nombre nuevo.
- D-14 aprobada: ISO de menos de 2 GiB publicada en GitHub Releases.

## [0.1.0] - 2026-11-20

### Añadido

- Análisis de viabilidad y propuesta de arquitectura con las decisiones D-01 a D-16.
- Hoja de ruta por fases hasta la versión 1.0.0.
- Guía de desarrollo: entorno, versionado y política de documentación.
- README, CHANGELOG y TODO bilingües (inglés y castellano).
