# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Versión en castellano: [CHANGELOG.es.md](CHANGELOG.es.md)

## [Unreleased]

### Added

- Arctiva archiso profile in `iso/`, derived from `releng` (archiso 92): Plasma with automatic login for the `live` user, UEFI-only boot, xz compression and the system package selection. Not yet built or tested.
- `build.sh`: reproducible build with an Arch Linux Archive date (`iso/archive-date`), `sha256` checksum and a 1.9 GiB limit.
- GitHub Actions workflow `iso.yml` with the build, a QEMU UEFI boot test (`tests/boot-test.sh`) and a weekly build.

## [0.1.7] - 2026-11-20

### Changed

- D-03: installer design settled on Calamares 3.4.3 (Qt 6): page order, QML pages (including the profile page with `packagechooserq` and a "Check" page), visual identity, and a launcher that detects BitLocker and Windows Fast Startup before partitioning, which Calamares does not do.
- D-04: optional LUKS1 encryption with `/boot` inside `@` and a single passphrase prompt in GRUB, with a warning about the US keyboard layout at boot; EFI partition at `/boot/efi`; the ISO boots in UEFI mode only.

### Fixed

- D-04: GRUB has supported Argon2 since 2.14 (Arch ships 2.16); LUKS2 is still left out because of the memory problems reported with the Argon2id settings Calamares uses.

## [0.1.6] - 2026-11-20

### Changed

- D-07 approved: the store will be an in-house module of Arctiva Center. It queries pacman on a temporary copy of the databases, installs with `pacman -Syu --needed`, manages Flatpak with libflatpak and `flatpak-kcm`, and shows the AUR PKGBUILD and its diff on every update. The installed system does not ship Discover, which stays on the live ISO only.
- D-09: Arctiva Center gains the "Applications" module.
- The logo in `branding/logo/` is approved (D-13).

## [0.1.5] - 2026-11-20

### Changed

- Architecture decisions D-01…D-16 approved, except D-07 (store), which is still under study.
- D-03 and D-05: warnings for dual boot with Windows (BitLocker cannot be resized from the installer, the recovery key is asked after changing Secure Boot, Fast Startup must be off).
- D-04: new `@snapshots` subvolume so Snapper can roll back, read-only snapshots boot through `grub-btrfs-overlayfs`, no hibernation in 1.0, and LUKS encryption limited to what GRUB supports.
- D-06: Wayland-only session, as KDE dropped the X11 session in Plasma 6.8.
- D-15: GitHub Actions runner disk space and the deactivation of scheduled workflows after 60 days without activity.

### Fixed

- D-10: the NVIDIA package for the LTS kernel is `nvidia-open-lts`.
- The hardware requirements reflect the already prepared build VM.

## [0.1.4] - 2026-11-20

### Changed

- The development guide documents the verified build VM setup and the stock `releng` ISO build, which boots in a test VM.
- The GitHub repository and the local remote now use the name `arctiva`.

## [0.1.3] - 2026-11-20

### Added

- Arctiva logo in `branding/logo/`: full logo, colour mark, monochrome mark and application icon (SVG).
- Logo at the top of both READMEs.

## [0.1.2] - 2026-11-20

### Added

- GPL-3.0-or-later licence (`LICENSE`), with CatLinux as copyright holder.
- Name and logo policy (`TRADEMARKS.md`): the brand is not covered by the code licence.
- Credits and license section in both READMEs.

## [0.1.1] - 2026-11-20

### Changed

- The project is renamed from Archtiva to Arctiva, including package, repository and ISO names.
- D-03: Calamares stays as the installation engine, with an interface rebuilt in QML and a Qt stylesheet so it carries the project's identity, without patching its code.
- D-07: the store will offer the official repositories, Flathub and the AUR as separate sources, with the AUR disabled by default and warnings; the concrete solution is now under study.
- D-13: identity updated for the new name.
- D-14 approved: an ISO under 2 GiB published on GitHub Releases.

## [0.1.0] - 2026-11-20

### Added

- Feasibility analysis and architecture proposal with decisions D-01 to D-16.
- Phased roadmap up to version 1.0.0.
- Development guide: environment, versioning and documentation policy.
- Bilingual README, CHANGELOG and TODO (English and Spanish).
