# Pendiente

> English version: [TODO.md](TODO.md)

Trabajo pendiente agrupado por prioridad. Fases y decisiones: [hoja de ruta](docs/es/hoja-de-ruta.md) · [arquitectura](docs/es/arquitectura.md).

## Alta: fase 0 (fundamentos)

- [ ] Decidir cuándo se hace público el repositorio.

## Media: seguimiento de la fase 1

- [ ] Compilar los paquetes propios (`packages/`) con la misma fecha del Arch Linux Archive que la ISO, para que Calamares no se compile con bibliotecas más nuevas que las incluidas.

## Media: fase 2 (instalador)

- [ ] Al arrancar una instantánea falla `systemd-remount-fs` (fstab pide `subvol=/@` y la raíz es un overlay de grub-btrfs). No impide arrancar; valorar ocultarlo.
- [ ] `/etc/os-release` dice «Arch Linux»: lo cambiará el paquete de identidad de Arctiva (`arctiva-branding`/`arctiva-settings`).
- [ ] Que el instalador elija mirrors rápidos (`reflector`) antes de `pacman -Syu`: el sistema instalado se queda con todos los mirrors HTTPS en el orden por defecto.
- [ ] Avisar en la página de resumen si la raíz no es Btrfs (modo manual): no habrá instantáneas (paso 2.4).
- [ ] Las páginas QML del instalador llevan sus textos en castellano, catalán e inglés dentro del propio QML; pasarlos a traducciones del branding (`.ts`) para poder añadir más idiomas.
- [ ] Mapa sin conexión en la página «Idioma y zona»: el de Calamares descarga los mosaicos de Internet, así que de momento la página usa solo listas.
- [ ] Perfiles Básico, Juegos y Oficina: `packagechooserq` solo admite una opción, así que hay que elegir entre `packagechooser` de widgets (`optionalmultiple`) y `netinstall`, y definir los paquetes de cada perfil (Juegos necesita `multilib`).
- [ ] Tras cambiar de idioma en la bienvenida, los textos de los requisitos siguen en el idioma en que se comprobaron (Calamares los genera antes de elegir): repetir la comprobación o traducirlos en la página.
- [ ] Pasar `zram-generator.conf` de `iso/airootfs/` al paquete `arctiva-settings` cuando exista.

## Media: estudios

- [ ] Prueba de concepto de la tienda (D-07) en la VM: catálogo AppStream, `pyalpm` sobre una base temporal, instalación con `pacman -Syu --needed` a través de un ayudante polkit, Flatpak con progreso y `flatpak-kcm`, y flujo del AUR con PKGBUILD, diff y `paru`. Antes de la fase 5.
- [ ] Comprobaciones del instalador en la VM, antes de la fase 2 (D-03, D-04): qué hacen y qué necesitan `localeq`, `packagechooserq` y `notesqml` de Calamares 3.4.3; `os-prober` con Windows, BitLocker e inicio rápido; alcance de `stylesheet.qss` en la página de disco.

## Más adelante

- Fases 2 a 7 según la hoja de ruta.
- Pruebas en hardware real (USB en el PC con la RTX 4060; portátil con Windows y Manjaro), solo al final, con todo implementado (fase 7). La entrada «safe graphics» ya funciona en VirtualBox.
- Convertir en trazos el lema de `branding/logo/arctiva-logo.svg`, que ahora es texto, cuando se elija la tipografía corporativa (D-13).
- Hibernación: subvolumen `@swap` con un archivo de intercambio además de zram (D-04). Queda fuera de la 1.0, que solo tiene suspensión.
- ISO reproducible bit a bit: dos construcciones con la misma fecha del Arch Linux Archive tienen los mismos paquetes y tamaño, pero distinta suma (D-02).
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
