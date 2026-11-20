# Arctiva

<p align="center"><img src="branding/logo/arctiva-logo.svg" width="360" alt="Arctiva"></p>

**Linux, without the barriers.**

> English version: [README.md](README.md)

Arctiva es una distribución Linux basada en Arch Linux. Conserva los repositorios oficiales de Arch, pacman y su modelo rolling release, y añade un instalador gráfico, un escritorio KDE Plasma cómodo para quien viene de Windows, actualizaciones sencillas con instantáneas automáticas, y controladores gráficos y juegos sin complicaciones.

Arctiva es un proyecto independiente, sin relación oficial con Arch Linux ni respaldo suyo.

## Estado

**Fase 1 terminada (0.2.0):** una ISO live con KDE Plasma que arranca hasta el escritorio. Aún no hay instalador (fase 2) ni ISO para descargar: se puede construir desde el código (ver la guía de desarrollo). La arquitectura está aprobada (decisiones D-01…D-16).

- [Arquitectura y decisiones](docs/es/arquitectura.md)
- [Hoja de ruta](docs/es/hoja-de-ruta.md)
- [Guía de desarrollo](docs/es/desarrollo.md)
- [Tareas pendientes](TODO.es.md) · [Registro de cambios](CHANGELOG.es.md)

## Requisitos previstos

- PC x86 de 64 bits con firmware UEFI (Secure Boot desactivado)
- 4 GB de RAM (8 GB recomendados)
- 40 GB de disco (64 GB recomendados)
- Gráfica compatible con Vulkan para jugar

## Instalación y uso

Todavía no hay ISO publicada. Para construir y probar la ISO live, sigue [Construir la ISO de Arctiva](docs/es/desarrollo.md#construir-la-iso-de-arctiva) en la guía de desarrollo.

## Créditos y licencia

**Arctiva** está desarrollado y mantenido por **CatLinux**.
Copyright (C) 2026 CatLinux.

Licencia [GPL-3.0-or-later](LICENSE): software libre que puedes usar para cualquier fin, también comercial, y estudiar, modificar y compartir. Si lo distribuyes, modificado o no, debes mantener la misma licencia y facilitar el código fuente.

El nombre y el logo de Arctiva no están cubiertos por esta licencia: ver [TRADEMARKS.es.md](TRADEMARKS.es.md).

Las copias y los forks deben conservar esta atribución y enlazar a https://github.com/catlinux/arctiva.

### Material de terceros

- `packages/calamares` compila [Calamares](https://calamares.io) (GPL-3.0-or-later, © los autores de Calamares) y `packages/ckbcomp` empaqueta `ckbcomp` de [console-setup](https://salsa.debian.org/installer-team/console-setup) (GPL-2.0-or-later, © Anton Zinoviev). Los PKGBUILD son GPL-3.0-or-later.
- `iso/` deriva del perfil `releng` de [archiso](https://gitlab.archlinux.org/archlinux/archiso) 92 (GPL-3.0-or-later, © los autores de archiso); los archivos adaptados y copiados conservan esa licencia.
