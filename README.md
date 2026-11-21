# Arctiva

<p align="center"><img src="branding/logo/arctiva-logo.svg" width="360" alt="Arctiva"></p>

**Linux, without the barriers.**

> Versión en castellano: [README.es.md](README.es.md)

Arctiva is a Linux distribution based on Arch Linux. It keeps Arch's official repositories, pacman and its rolling-release model, and adds a graphical installer, a Windows-friendly KDE Plasma desktop, simple updates with automatic snapshots, and hassle-free gaming and graphics drivers.

Arctiva is an independent project. It is not affiliated with or endorsed by Arch Linux.

## Status

**Phase 5 completed (0.6.0):** Arctiva's own look: a Windows-style desktop (centred taskbar, start menu with search), light and dark modes, the "Orbit" wallpaper, a GRUB theme and a Plymouth boot screen, a "Personalization" page in Arctiva Center with "Restore the Arctiva look", the Outfit typeface and snapshot limits. Tested in a full encrypted install in a virtual machine.

**Phase 4 completed (0.5.0):** a live ISO with KDE Plasma and a graphical installer (Calamares) with Basic, Gaming and Office profiles, Btrfs with bootable snapshots, optional encryption and installation alongside Windows, tested in virtual machines. The installed system updates from a signed in-house repository (`[arctiva]`) and installs the graphics drivers. Arctiva Center has the welcome screen, updates, drivers and extras, tested with a full encrypted install. There is no ISO to download yet: it can be built from the source (see the development guide). The architecture is approved (decisions D-01…D-16).

- [Architecture and decisions](docs/en/architecture.md)
- [Roadmap](docs/en/roadmap.md)
- [Development guide](docs/en/development.md)
- [Pending tasks](TODO.md) · [Changelog](CHANGELOG.md)

## Planned system requirements

- 64-bit x86 PC with UEFI firmware (Secure Boot disabled)
- 4 GB RAM (8 GB recommended); the idle desktop uses about 1.2 GB
- 25 GB of disk space (40 GB recommended, for snapshots); the base system takes about 5 GB
- A Vulkan-capable GPU for gaming
- A USB stick of 4 GB or more for the installation media

## Installation and usage

No ISO is published yet. To build and try the live ISO, follow [Building the Arctiva ISO](docs/en/development.md#building-the-arctiva-iso) in the development guide.

## Credits and license

**Arctiva** is developed and maintained by **CatLinux**.
Copyright (C) 2026 CatLinux.

Licensed under [GPL-3.0-or-later](LICENSE): free software that you can use for any purpose, including commercial use, and study, modify and share. If you distribute it, modified or not, you must keep the same licence and provide the source code.

The Arctiva name and logo are not covered by this licence: see [TRADEMARKS.md](TRADEMARKS.md).

Copies and forks must keep this attribution and link to https://github.com/catlinux/arctiva.

### Third-party material

- `packages/calamares` builds [Calamares](https://calamares.io) (GPL-3.0-or-later, © the Calamares authors) and `packages/ckbcomp` packages `ckbcomp` from [console-setup](https://salsa.debian.org/installer-team/console-setup) (GPL-2.0-or-later, © Anton Zinoviev). The PKGBUILDs are GPL-3.0-or-later.
- `iso/` is derived from the `releng` profile of [archiso](https://gitlab.archlinux.org/archlinux/archiso) 92 (GPL-3.0-or-later, © the archiso authors); adapted and copied files keep that licence.
- `packages/arctiva-branding/files/color-schemes/ArctivaLight.colors` derives from `BreezeLight.colors` of [Breeze](https://invent.kde.org/plasma/breeze) (LGPL-2.0-or-later, © the KDE authors) and keeps that licence.
- The Plymouth themes in `arctiva-branding` use the password-dialog images (`lock`, `entry`, `bullet`, `capslock`, `keyboard`, `keymap-render`) of the `spinner` theme of [Plymouth](https://www.freedesktop.org/wiki/Software/Plymouth/) (GPL-2.0-or-later, © the Plymouth authors), copied from the `plymouth` package when `arctiva-branding` is built.
- `branding/fonts/` contains [Outfit](https://github.com/Outfitio/Outfit-Fonts) (SIL Open Font License 1.1, © The Outfit Project Authors); its licence is in `branding/fonts/OFL.txt`. The tagline of the logo is that font converted to paths.
