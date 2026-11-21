# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Versión en castellano: [CHANGELOG.es.md](CHANGELOG.es.md)

## [Unreleased]

## [0.3.10] - 2026-11-21

Patch release: documentation only.

### Changed

- Roadmap: signed `[arctiva]` repository marked as done. The first publication (five packages) and the check from a clean system with `SigLevel = Required` passed in CI.

## [0.3.9] - 2026-11-21

### Fixed

- Repository check: the keyring signature is saved under another name, so that `pacman -U` does not require a key that is not in the keyring yet.

## [0.3.8] - 2026-11-21

### Fixed

- Repository publishing: the logo needed by `arctiva-branding` is copied into the build directory, the database is copied over the links left by `repo-add`, and a stray argument in the upload command was removed. The whole script was tested in an `archlinux` container with a throwaway key.

## [0.3.7] - 2026-11-21

### Fixed

- Repository publishing: the build user could not enter the temporary working directory (created with mode 700), so no package was built.

## [0.3.6] - 2026-11-21

Signed `[arctiva]` repository (phase 3, steps 3.3 and 3.4). Patch release: nothing is published until the first push.

### Added

- `arctiva-keyring` package with the repository's public key, trusted at full level, in the ISO and the installed system.
- `Repositorio` workflow and `packages/publish-repo.sh`: build, sign and publish the `arctiva-*` packages to `catlinux/arctiva-repo`, then check that a clean system can install from it with `SigLevel = Required`.
- The installed system gets the `[arctiva]` section at the end of the installation, with its server in `/etc/pacman.d/arctiva-mirrorlist` (`arctiva-settings` 0.1.1).

## [0.3.5] - 2026-11-21

Arctiva Center skeleton (phase 4, step 4.1). Patch release: new package with no functionality yet.

### Added

- `center/`: Arctiva Center window (PySide6, QML and Kirigami) with the Welcome, Updates, Drivers and Extras sidebar, launcher (`--welcome`, `--check`, `--module`), Spanish and Catalan translations, minimal data catalogues and `pytest` tests.
- `arctiva-center` package, published to `[arctiva]` and included in the ISO; `center/**` triggers the repository and ISO workflows.

## [0.3.4] - 2026-11-21

Previous checks for Arctiva Center on the live ISO. Patch release: documentation only.

### Changed

- Architecture (D-08): arch-update evaluated and rejected as a dependency (AUR-only, terminal and tray tool); `checkupdates`, the RSS feed and `pacdiff` are used directly. `arctiva-center` will depend on `fakeroot`, which `checkupdates` needs and `pacman-contrib` does not declare.
- Roadmap: arch-update evaluation marked as done.

## [0.3.3] - 2026-11-21

Arctiva Center design and roadmap updates. Patch release: documentation only.

### Changed

- Architecture (D-09): Arctiva Center design for phase 4 (QML and Kirigami interface, `pkexec` helper with a closed set of operations, update reminder timer, GRUB hook).
- Roadmap: phase 4 adds reinstalling GRUB on the EFI partition when the `grub` package is upgraded; phase 6 adds a graphical GRUB theme.

## [0.3.2] - 2026-11-21

GPU detection and driver installation (D-10). Patch release, per the project's versioning policy for phase 3 steps.

### Added

- Package `arctiva-hardware` with `arctiva-gpu`, which reads `lspci -nn` and decides the drivers: NVIDIA Turing or later (PCI id `>= 0x1E00`) gets `nvidia-open` and `nvidia-utils` (plus `nvidia-open-lts` with the LTS kernel and `lib32-nvidia-utils` with Steam); older NVIDIA keeps `nouveau` with a notice; AMD and Intel need nothing extra; two or more real GPUs enable `switcheroo-control`.
- Installer step that installs those drivers after the packages and before the initramfs is generated, with early NVIDIA KMS. Without a connection, or if anything fails, the installation continues with the free driver.
- "Computer check" page: notices for modern NVIDIA (needs a connection) and for older NVIDIA (uses `nouveau`).
- `tests/gpu-detect-test.sh` with `lspci` fixtures.

## [0.3.1] - 2026-11-21

Phase 3, first step: the identity packages of the installed system. Patch release: it adds no installer behaviour.

### Added

- Package `arctiva-settings`: zram configuration (moved from the ISO), a pacman hook that rewrites `/usr/lib/os-release` so the system identifies itself as Arctiva after every `filesystem` update, and the `reflector` configuration. The installed system enables `reflector.timer`.
- Package `arctiva-branding`: the distribution logo and the Plasma "About this system" configuration.
- Guide to the repository signing keys ([docs/en/signing.md](docs/en/signing.md)).

### Changed

- D-01: `[arctiva]` only holds what the installed system uses; `calamares`, `ckbcomp` and the installer configuration stay ISO-only. D-10: the NVIDIA rule is the PCI device id (`>= 0x1E00`).

## [0.3.0] - 2026-11-21

Phase 2 closed: the installer is complete and tested in virtual machines (UEFI, QEMU/KVM). Tested: erase disk, with and without encryption; manual partitioning (own ESP and Btrfs root); "Install alongside" a simulated Windows (NTFS shrunk, ESP reused, `os-prober` adds Windows to GRUB); profiles with and without a connection. Tests with real Windows and real hardware stay for phase 7.

### Added

- Development guide: how to test alongside installs and manual partitioning, and the disk size they need.

## [0.2.8] - 2026-11-21

Phase 2, profiles (second part): appearance, summary and sizes. Awaiting the user's approval with screenshots.

### Added

- Profiles page styled with the installer palette (cards, selected item with border and background) and one image per profile (`perfil-juegos.svg`, `perfil-oficina.svg`, `perfil-basico.svg`).
- "Basic" entry in the list, explaining that it is always installed and how to add the others (hold Ctrl and click: the list uses extended selection).
- "Profiles" card on the summary page with what was chosen, deduced from the package operations left by the page.

### Fixed

- `tests/fake-windows-disk.sh` also creates `EFI/Microsoft/Boot/BCD`: without it `os-prober` does not recognise the simulated Windows and GRUB gets no entry for it.

### Changed

- Gaming and Office descriptions include the download size (about 0.3 GB each, measured with `pacman -Sp` against the ISO's base).

## [0.2.7] - 2026-11-20

Phase 2, profiles (first part): configuration and multilib. Appearance, summary and download sizes follow in 0.2.8.

### Added

- "Profiles" installer page (widget `packagechooser`, several choices allowed) with Gaming and Office. Basic is what the ISO already carries and is always installed. The packages are installed from the repositories when there is a connection; offline, only Basic is installed.

### Changed

- `multilib` is enabled on the installed system.

### Changed

- Phase 2, step 4 closed: the user approves the installer interface with screenshots (sidebar, navigation, own QML pages and slideshow from 0.2.4–0.2.6).

## [0.2.6] - 2026-11-20

Phase 2, step 4 (second part): Arctiva's own installer QML pages. Awaiting the user's approval with screenshots. Profiles are postponed: `packagechooserq` only allows one choice.

### Added

- Arctiva QML pages for welcome, language and region, keyboard, account, summary and finish, with the mock-up colours and texts in Spanish, Catalan and English. Language and region works offline (lists instead of Calamares' map, which downloads its tiles from the Internet). The keyboard page searches layouts and has a test field; the account page shows password strength.
- Own slideshow during the installation: snapshots, Plasma, an up-to-date Arch base and encryption.
- `build.sh -c <dir>`: a local repository kept between builds; only what changes version is rebuilt (the installer configuration, always). Avoids building Calamares for every ISO.

### Changed

- The installer uses Calamares' QML modules (`welcomeq`, `localeq`, `keyboardq`, `usersq`, `summaryq`, `finishedq`) instead of the widget ones, except for the disk page.

## [0.2.5] - 2026-11-20

Installer fix (patch). Tested in QEMU with the 0.2.5 ISO: the installed system boots without Discover or Calamares; the two remaining 0.2.4 changes were also checked (BitLocker detected with `blkid -p` and translated step names).

### Fixed

- Discover was still on the installed system and showed "Update problem" when opened: target preparation now removes it along with Calamares (D-07; it stays on the live ISO).

### Changed

- Real-hardware tests (PC with NVIDIA and laptop with Windows and Manjaro) move to phase 7: they will be done at the end, with everything implemented. Phase 2 closes with virtual-machine tests.

## [0.2.4] - 2026-11-20

Phase 2, step 4 (first part): installer identity. Awaiting the user's approval with screenshots; the QML pages (`*q`) and the slideshow are left for the second part. "Install alongside" was also tested in QEMU (80 GB disk, simulated 60 GB NTFS): Calamares shrinks it with `ntfsresize`, installs and boots, and the NTFS stays healthy; `os-prober` does not recognise the simulated Windows and will be checked with a real one (step 2.5).

### Added

- Installer sidebar and navigation in QML, following the mock-ups: night-blue gradient, Arctiva symbol and version, numbered steps (the current one in a blue pill, finished ones ticked), "Next" in blue and "Done" as the main button on the last page.
- `stylesheet.qss` for the widget pages (partitioning, users, summary) with the logo palette; the logo and icon are taken from `branding/logo/` when packaging.

### Fixed

- Calamares' own "Install System" entry was still in the live menu next to "Install Arctiva": the live setup now removes it.

## [0.2.3] - 2026-11-20

Phase 2, step 3: launcher and "Check" page. Tested in QEMU with a disk that simulates Windows (all three levels); a test with a real Windows 11 is still pending (step 2.5).

### Added

- `arctiva-installer` launcher ("Install Arctiva" menu entry, which replaces Calamares' own): checks the machine with `detect-system` and opens Calamares. It detects Windows (`bootmgfw.efi` on an ESP), BitLocker partitions, hibernated NTFS (`ntfs-3g.probe`, exit code 14), running on battery and Internet access, and writes the result to `/run/arctiva/equipo.json`.
- "Check" page (`notesqml`) before the disk page, in Spanish, Catalan and English following the chosen language: block (Windows hibernated or with Fast Startup, with a button to quit), warning (BitLocker, battery) or OK, plus notes on the Windows clock and on a missing network.
- `tests/fake-windows-disk.sh`: simulates a disk with a clean, hibernated or BitLocker Windows in the VM.
- `ntfsprogs` on the ISO: `ntfsresize`, which KPMcore needs to shrink Windows, is no longer part of `ntfs-3g`.

### Changed

- D-03: the block level is a recommendation (Calamares does not let QML disable "Next"); what prevents installing alongside a hibernated Windows is `ntfsresize`.

## [0.2.2] - 2026-11-20

Phase 2, step 2: base installer configuration (no custom interface yet). Tested in QEMU with UEFI: erase-disk install, unencrypted and encrypted, booting the installed system, `snapper list` and booting the initial snapshot from GRUB (also with an encrypted root; GRUB unlocks in about 5 s).

### Added

- `arctiva-calamares-config` package in `installer/` (goes to `/etc/calamares/` on the live ISO and is removed from the installed system): page sequence with the widget modules, Btrfs with `@`, `@home`, `@cache`, `@log` and `@snapshots`, no disk swap, optional LUKS1 encryption with a single passphrase in GRUB, GRUB in `EFI/arctiva` with `os-prober`, a `BOOTX64.EFI` fallback copy, `linux` as the default entry, an "Arctiva snapshots" submenu and without GRUB 2.16's "EFI BootNext" entries, classic mkinitcpio hooks with `grub-btrfs-overlayfs`, system services, and `linux-lts` (after a `pacman -Syu`) when online.
- Installer scripts: `prepare-target` (copies the kernel, which mkarchiso leaves out of `/boot`; removes Calamares and `mkinitcpio-archiso`; initialises the pacman keyring; uses the live system's DNS during the install) and `finish-target` (restores the original `resolv.conf`, Snapper on `@snapshots`, an initial "Arctiva: estado inicial" snapshot and a GRUB menu that lists it).
- zram (half of RAM, at most 8 GiB) on the live and installed systems, and `inotify-tools` for `grub-btrfsd`.

### Changed

- `packages/build-packages.sh` also builds `arctiva-calamares-config`, and CI runs on changes to `installer/`.
- The live session no longer locks the screen when idle (it locked in the middle of an install).
- `tests/run-live.sh` always boots the ISO first when given one, even if the NVRAM remembers another order.

## [0.2.1] - 2026-11-20

Phase 2, step 1: installer packages.

### Added

- `packages/calamares` PKGBUILD (Calamares 3.4.3, Qt6, source signature verified against the maintainer's key) and `packages/ckbcomp` (from console-setup 1.249, checksum pinned).
- `packages/build-packages.sh` builds them into a local `arctiva-local` pacman repository; `build.sh` does it automatically, or uses a prebuilt one with the new `-l` option.
- `calamares` is part of the live ISO (1.76 GiB).

## [0.2.0] - 2026-11-20

Phase 1 completed: minimal live ISO.

### Added

- Arctiva archiso profile in `iso/`, derived from `releng` (archiso 92): Plasma with automatic login for the `live` user, UEFI-only boot, xz compression and the system package selection. Built and tested in VirtualBox: it reaches the desktop and takes 1.75 GiB.
- `build.sh`: reproducible build with an Arch Linux Archive date (`iso/archive-date`), `sha256` checksum, a 1.9 GiB limit and a `-k` option to keep the working directory.
- GitHub Actions workflow `iso.yml` with the build, a QEMU UEFI boot test (`tests/boot-test.sh`) and a weekly build. The first run passes.
- `tests/boot-test.sh` no longer needs root when `7z` is available.
- Detailed plan with checkboxes for every phase in the roadmap.
- `tests/run-live.sh`: boots the ISO in QEMU/KVM with a virtual disk and shows it in the browser with noVNC.
- The workflow uses `actions/checkout` and `actions/upload-artifact` v7 (Node.js 24), as Node.js 20 is deprecated on the runners.

### Changed

- D-04 and D-14: `linux-lts` is installed during installation when a connection is available instead of shipping on the ISO, and the ISO leaves out package documentation; this brings it down from 2.12 to 1.75 GiB. Size measured and broken down in D-14.

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
