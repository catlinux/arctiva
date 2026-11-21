# Registro de cambios

Todos los cambios relevantes del proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/).

> English version: [CHANGELOG.md](CHANGELOG.md)

## [Sin publicar]

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
