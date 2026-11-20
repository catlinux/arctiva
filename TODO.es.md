# Pendiente

> English version: [TODO.md](TODO.md)

Trabajo pendiente agrupado por prioridad. Fases y decisiones: [hoja de ruta](docs/es/hoja-de-ruta.md) · [arquitectura](docs/es/arquitectura.md).

## Alta: fase 0 (fundamentos)

- [ ] Aprobar el logo nuevo de `branding/logo/` (D-13). El lema de `arctiva-logo.svg` es texto: convertirlo en trazos cuando se elija la tipografía corporativa.
- [ ] Decidir cuándo se hace público el repositorio.

## Media: fase 1 (ISO live mínima)

- [ ] Perfil archiso de Arctiva derivado de `releng`, con Plasma e inicio de sesión automático en el live.
- [ ] Script de construcción reproducible con una fecha fijada del Arch Linux Archive.
- [ ] Flujo de GitHub Actions: construcción de la ISO y prueba de arranque en QEMU.
- [ ] Medir el tamaño de la ISO y confirmar que no pasa de 2 GiB (D-14).

## Media: estudios

- [ ] Estudio de la tienda y sus fuentes (D-07): comparar Discover con un motor propio, Pamac, Bauh, Octopi y una tienda propia; prueba de concepto y decisión final.
- [ ] Diseño de la interfaz del instalador (D-03): maquetas de las páginas QML y de la hoja de estilo del particionado, antes de la fase 2.

## Más adelante

- Fases 2 a 7 según la hoja de ruta.
- Hibernación: subvolumen `@swap` con un archivo de intercambio además de zram (D-04). Queda fuera de la 1.0, que solo tiene suspensión.

## Descartado

- **Bifurcar o retener paquetes oficiales de Arch:** rompe la compatibilidad con el AUR y multiplica el mantenimiento (D-01).
- **Motor PackageKit de Discover:** mal soporte en Arch y riesgo de actualizaciones parciales (D-07).
- **Instalador escrito desde cero:** el particionado y el redimensionado de Windows es donde se pierden datos; en su lugar se personaliza Calamares (D-03).
- **BIOS heredada en la 1.0:** duplica la matriz de pruebas con muy poco beneficio (D-04).
- **Partir la ISO en trozos:** las herramientas para grabar USB necesitan un único archivo (D-14).
- **Paquete nativo de Bottles:** sus desarrolladores solo soportan Flatpak (D-12).
