# Pendiente

> English version: [TODO.md](TODO.md)

Trabajo pendiente agrupado por prioridad. Fases y decisiones: [hoja de ruta](docs/es/hoja-de-ruta.md) · [arquitectura](docs/es/arquitectura.md).

## Alta: fase 0 (fundamentos)

- [ ] Decidir cuándo se hace público el repositorio.

## Media: fase 1 (ISO live mínima)

- [ ] Perfil archiso de Arctiva derivado de `releng`, con Plasma e inicio de sesión automático en el live; arranque solo UEFI (D-04).
- [ ] Script de construcción reproducible con una fecha fijada del Arch Linux Archive.
- [ ] Flujo de GitHub Actions: construcción de la ISO y prueba de arranque en QEMU.
- [ ] Medir el tamaño de la ISO y confirmar que no pasa de 2 GiB (D-14).

## Media: estudios

- [ ] Prueba de concepto de la tienda (D-07) en la VM: catálogo AppStream, `pyalpm` sobre una base temporal, instalación con `pacman -Syu --needed` a través de un ayudante polkit, Flatpak con progreso y `flatpak-kcm`, y flujo del AUR con PKGBUILD, diff y `paru`. Antes de la fase 5.
- [ ] Comprobaciones del instalador en la VM, antes de la fase 2 (D-03, D-04): qué hacen y qué necesitan `localeq`, `packagechooserq` y `notesqml` de Calamares 3.4.3; que la página «Comprobación» puede leer el resultado del lanzador; instalación cifrada con una sola contraseña y tiempo de desbloqueo en GRUB; arrancar una instantánea con la raíz cifrada; `os-prober` con Windows, BitLocker e inicio rápido; alcance de `stylesheet.qss` en la página de disco.

## Más adelante

- Fases 2 a 7 según la hoja de ruta.
- Convertir en trazos el lema de `branding/logo/arctiva-logo.svg`, que ahora es texto, cuando se elija la tipografía corporativa (D-13).
- Hibernación: subvolumen `@swap` con un archivo de intercambio además de zram (D-04). Queda fuera de la 1.0, que solo tiene suspensión.
- Cifrado LUKS2 con desbloqueo por TPM2 o FIDO2, cuando Calamares permita elegir el método de derivación de la clave (D-04).
- Contraseña de cifrado con la distribución de teclado del usuario en GRUB (`grub-kbdcomp`), en lugar de la estadounidense (D-04).

## Descartado

- **Bifurcar o retener paquetes oficiales de Arch:** rompe la compatibilidad con el AUR y multiplica el mantenimiento (D-01).
- **Motor PackageKit de Discover:** mal soporte en Arch y riesgo de actualizaciones parciales (D-07).
- **Discover con un motor propio, Pamac, Bauh u Octopi como tienda:** sin motor para pacman en Discover y sin interfaz estable para escribirlo; los demás dependen del AUR, están parados o no tienen Flatpak (D-07).
- **Instalador escrito desde cero:** el particionado y el redimensionado de Windows es donde se pierden datos; en su lugar se personaliza Calamares (D-03).
- **LUKS2 con Argon2id o `/boot` sin cifrar en la 1.0:** con Argon2id hay informes de GRUB sin memoria al arrancar, y un `/boot` aparte rompe las instantáneas arrancables (D-04).
- **BIOS heredada en la 1.0:** duplica la matriz de pruebas con muy poco beneficio (D-04).
- **Partir la ISO en trozos:** las herramientas para grabar USB necesitan un único archivo (D-14).
- **Paquete nativo de Bottles:** sus desarrolladores solo soportan Flatpak (D-12).
