# Pendiente

> English version: [TODO.md](TODO.md)

Trabajo pendiente agrupado por prioridad. Fases y decisiones: [hoja de ruta](docs/es/hoja-de-ruta.md) · [arquitectura](docs/es/arquitectura.md).

## Alta: fase 0 (fundamentos)

- [ ] Revisar y aprobar las decisiones de arquitectura D-01 a D-16.
- [ ] Elegir y aplicar la licencia del proyecto.
- [ ] Consultar a `trademarks@archlinux.org` si el nombre «Archtiva» es aceptable (D-13).
- [ ] Rediseñar el logo para que no se parezca al de Arch, con versiones vectorial (SVG) y monocroma (D-13).
- [ ] Ampliar la VM de construcción «Archtiva» (4–6 vCPU, 8 GB de RAM, 80 GB de disco) e instalar Arch Linux con `archiso`.
- [ ] Construir en la VM la ISO `releng` oficial y documentar los pasos comprobados en la guía de desarrollo.
- [ ] Decidir cuándo se hace público el repositorio.

## Media: fase 1 (ISO live mínima)

- [ ] Perfil archiso de Archtiva derivado de `releng`, con Plasma e inicio de sesión automático en el live.
- [ ] Script de construcción reproducible con una fecha fijada del Arch Linux Archive.
- [ ] Flujo de GitHub Actions: construcción de la ISO y prueba de arranque en QEMU.
- [ ] Medir el tamaño de la ISO y confirmar la estrategia de GitHub Releases (D-14).

## Más adelante

- Fases 2 a 7 según la hoja de ruta.

## Descartado

- **Bifurcar o retener paquetes oficiales de Arch:** rompe la compatibilidad con el AUR y multiplica el mantenimiento (D-01).
- **Motor PackageKit de Discover:** mal soporte en Arch y riesgo de actualizaciones parciales (D-07).
- **AUR dentro de la tienda:** código sin revisar al alcance de usuarios no técnicos (D-07).
- **Pamac:** pensado para los repositorios de Manjaro; se ha roto con actualizaciones importantes de pacman.
- **BIOS heredada en la 1.0:** duplica la matriz de pruebas con muy poco beneficio (D-04).
- **Partir la ISO en trozos:** las herramientas para grabar USB necesitan un único archivo (D-14).
- **Paquete nativo de Bottles:** sus desarrolladores solo soportan Flatpak (D-12).
