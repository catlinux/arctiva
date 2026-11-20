# Registro de cambios

Todos los cambios relevantes del proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/).

> English version: [CHANGELOG.md](CHANGELOG.md)

## [Sin publicar]

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
