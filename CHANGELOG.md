# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Versión en castellano: [CHANGELOG.es.md](CHANGELOG.es.md)

## [Unreleased]

### Added

- Arctiva Games 0.1.0: new optional package (`arctiva-games`, with its own window and menu entry) that installs Windows game launchers (Battle.net, EA app, Ubisoft Connect, GOG Galaxy, Epic Games) from our own recipes, or any installer found on lutris.net, step by step: summary of what will be downloaded and run before starting, live log saved to disk, retry / skip / stop at any step, a "Continue" button for launchers where you must sign in (they are not closed), a list of the Wine processes of the game, and a library with Play and Uninstall. It uses the system `wine` and `winetricks` (dependencies). Not yet tested on real hardware.
- Arctiva Center 0.7.10: new "Arctiva Games" extra in Extras, which installs that package.

### Changed

- Num Lock is now on by default when the session starts, in the live session and the installed system (`arctiva-settings` 0.5.2, `/etc/xdg/kcminputrc`). The login screen also requests it (`Numlock=on` in Plasma Login), still untested.

## [0.8.0] - 2026-11-22

First beta candidate: welcome and desktop icons in the live session and the installed system, installer and Arctiva Center fixes. Minor version (step 7.5 of phase 7: beta).

### Added

- The live session opens the Arctiva Center welcome at login, with an "Install Arctiva" button, and puts an "Install Arctiva" icon on the `live` user's desktop (Arctiva Center 0.7.9).
- A "Home" icon on the desktop of every new user, in the live session and the installed system (`arctiva-branding` 0.6.3, through `/etc/skel`). The desktop is pinned to `~/Desktop` so the icon also shows with the system in Spanish or Catalan.
- Arctiva Center: installing an extra now warns first that the download can take from minutes to over half an hour, and during installation (extras and applications) it shows a progress bar, the current step and the elapsed time. The bar is real with pacman (package n of m) and indeterminate with Flatpak, which gives no percentage.

### Fixed

- If you connect to the internet after opening the installer, `linux-lts` and the profiles are now installed anyway: Calamares checked the network only once at startup and `packages` skipped the installation even when a connection was available. A new job (`arctivanet`) checks again right before. The "Requirements" page still shows the startup state.
- The ISO build no longer aborts when `archive.archlinux.org` is slow from the GitHub runners (pacman gave up after 10 s under 1 B/s): `DisableDownloadTimeout`, 3 parallel downloads and up to 3 build attempts in the `ISO` and release workflows.

### Changed

- The welcome is no longer skipped in the live session; on the installed system it still appears on its own until it is switched off.
- The requirement texts on the installer's welcome page now follow the chosen language (Spanish, Catalan or English) instead of staying in the language of the startup.
- The "Windows programs" description no longer says it is only 0.2 GB: the program is, but the first time Flatpak also downloads its shared components.
- `release.yml`: checks the signing secrets before building, aligns the build container with the Archive date and publishes the notes in English and Spanish.
- User guide: Ventoy only boots in "grub2 mode", boot time from USB, the live welcome and a Btrfs root for manual partitioning.
- `tests/install-test.sh` waits up to 30 minutes for the installation to finish and detects the final button at two points of the button, away from its text.

## [0.7.4] - 2026-11-22

Boot test fix. Patch version.

### Fixed

- The live ISO announces on the console when the graphical session of the `live` user is up (`arctiva-live-ready.service`): the boot test looked for a systemd message that is no longer printed, so it never found the session even though the desktop started (checked in QEMU).

## [0.7.3] - 2026-11-22

Release workflow, user guide and hardware test matrix (phase 7, steps 7.2 to 7.4). Patch version.

### Added

- `.github/workflows/release.yml`: on a `vX.Y.Z` tag, builds the ISO with the pinned Archive date (no fallback), boot-tests it, signs it with the repository's signing subkey, verifies checksum and signature and creates the release. `docs/en/releasing.md` explains it and how to verify a download.
- User guide (`docs/en/user/`): preparing the USB, Secure Boot and BitLocker, installing, first steps, snapshots, games, Windows programs and the store.
- Real-hardware test matrix (`docs/en/testing.md`).

## [0.7.2] - 2026-11-22

Installer debts and a CI fallback (phase 7, step 7.0). Patch version.

### Added

- The installer sorts the mirrors with `reflector` (60 s limit, only with a connection; if it fails the default list stays) and checks the connection right before installing packages, leaving a clear warning in the log when it has dropped.
- `build.sh`: with `ARCHIVE_FALLBACK_LATEST=1`, if no Arch Linux Archive server answers it uses the current mirrors with a warning (the ISO workflow sets it so a checking build still works during an Archive outage; a published ISO must not).

## [0.7.1] - 2026-11-22

Small fixes found while taking screenshots. Patch version.

### Fixed

- GRUB theme (`arctiva-branding` 0.6.2): the menu is wider, so the description of the snapshots is no longer cut.
- Arctiva Center 0.7.8: the application detail page shows the Arch version and size also the first time, before the temporary database exists (it reads the system one, read-only).

## [0.7.0] - 2026-11-22

Phase 6 closed: applications and Windows. Tested on 2026-11-22 on an installed system in QEMU (store search, installs and removals from Arch and Flathub, AUR with review and update diff, `.exe` dialog with Bottles, Flatpak extras) and with the ISO built in a container. Minor version (phase completed, D-16). No code changes since 0.6.7.

## [0.6.7] - 2026-11-22

Discover out of the live ISO (phase 6, step 6.6). Patch version.

### Removed

- The live ISO no longer includes Discover: the store is Arctiva Center's "Applications" page, which in the live session shows the catalogue with its actions disabled.

## [0.6.6] - 2026-11-22

Windows programs and Flatpak extras (phase 6, step 6.5). Patch version.

### Added

- Arctiva Center 0.7.7: "Windows programs" (Bottles), "Heroic Games Launcher" and "ProtonPlus" extras, installed from Flathub with Flatpak (`flatpaks` field in `extras.toml`).
- Double-clicking a `.exe` or `.msi` (Dolphin asks first whether to launch it) opens a dialog (`arctiva-center --windows-app <file>`) that explains what will happen, installs Bottles if it is missing, opens the file with Bottles and links to WineHQ AppDB, ProtonDB and Are We Anti-Cheat Yet?. It is the default application for those file types.

## [0.6.5] - 2026-11-22

AUR in the store (phase 6, step 6.4). Patch version.

### Added

- Arctiva Center 0.7.6: AUR support, off by default and turned on in Applications after a warning. Search through the AUR RPC, a mandatory review (PKGBUILD and `.install` of every package to build, votes, maintainer, dates and reinforced warnings for orphaned, recent, out-of-date or barely voted packages), dependency chain, build as the user with `makepkg` and installation through the helper. AUR updates are manual and show the diff since the installed commit.

### Changed

- D-07: the AUR is built with `makepkg` instead of `paru`.

## [0.6.4] - 2026-11-22

"Applications" page in Arctiva Center (phase 6, step 6.3). Patch version.

### Added

- Arctiva Center 0.7.5: "Applications" module after Updates, with search, categories, featured applications and a detail page with one row per source (Arch, Flathub), version, size, the recommended source and screenshots. Arch applications are installed and removed through the helper; Flathub ones with Flatpak (system installation, with a log), with a "Permissions" button. If updates are pending, installing from Arch first takes you to Updates (no partial updates) and the installation waits for you.

## [0.6.3] - 2026-11-22

Store operations in the privileged helper (phase 6, step 6.2). Patch version.

### Added

- Arctiva Center 0.7.4, helper: `app-install` (`pacman -Syu --needed`), `app-remove` (refuses protected packages, packages not installed explicitly and removals that would drag a protected one, with a dry run first), `aur-prepare` (`base-devel` and `git`), `aur-deps` (only when no updates are pending) and `aur-install` (only packages already built by the user in `~/.cache/arctiva-center/aur/build/`, installed from a root-made copy). The list of protected packages is `data/protected.toml`.

## [0.6.2] - 2026-11-22

Store catalogue and queries (phase 6, step 6.1). Patch version.

### Added

- Arctiva Center 0.7.3: application catalogue (`core/appstream.py`) read from the Arch and Flathub AppStream files, merged by application, with accent-insensitive search, categories, the recommended source (Arch over Flathub, never the AUR, with exceptions in `data/sources.toml`), the featured list (`data/featured.toml`) and a cache; read-only pacman queries with `pyalpm` on the temporary database (`core/alpm_query.py`).
- New dependencies: `pyalpm`, `archlinux-appstream-data` and `flatpak-kcm`.

## [0.6.1] - 2026-11-22

Store proof of concept (phase 6, step 6.0). Documentation only; patch version.

### Changed

- Design of the store adjusted after testing on an installed system: the catalogue is read from the AppStream XML files with a cache, Flatpak runs through its command line, the AUR needs `base-devel` and `git`, and `flatpak-kcm` and `pyalpm` become dependencies.

## [0.6.0] - 2026-11-21

Phase 5 closed: identity and desktop. Tested on 2026-11-21 with an ISO built in a container and a full encrypted install in QEMU (themed GRUB menu, Plymouth, login screen, Windows-style desktop, Personalization page, snapshot limit). Minor version (phase completed, D-16).

### Fixed

- Plymouth showed nothing (`two-step` needs the password-dialog images in the theme folder): they are now copied from the `plymouth` package when `arctiva-branding` 0.6.1 is built.
- Snapper's cleanup never removed recent snapshots (`NUMBER_MIN_AGE` was one hour): it is now 0, so the limit of 10 is honoured right away.
- `splash` was added twice to the kernel command line (Calamares already adds it with Plymouth installed).
- Personalization: the accent colour is read from the colour scheme (Plasma has no `AccentColor` key), dark mode applies Arctiva's blue accent, and the selected accent swatch stays marked.
- GRUB theme: no more arrows (Outfit lacks them) and the countdown has a text.

## [0.5.10] - 2026-11-21

Installer and Arctiva Center identity. Patch version (phase 5 is still in progress).

### Added

- `arctiva-branding` 0.6.0 installs the Outfit typeface (SIL OFL 1.1, with its licence in `/usr/share/licenses/arctiva-branding/`).
- A "Make it yours" slide in the installer's slideshow, about the Personalization page.

### Changed

- Page titles and slideshow headings of the installer, and the welcome heading of Arctiva Center 0.7.1, use Outfit.

## [0.5.9] - 2026-11-21

Login screen. Patch version (phase 5 is still in progress).

### Added

- `arctiva-settings` 0.5.1: `/etc/plasmalogin.conf.d/arctiva-greeter.conf` sets Arctiva's dark wallpaper on the Plasma Login screen. Plasma Login only lets you change the wallpaper (colours and font are fixed, Breeze style).
- `arctiva-branding` 0.5.1: the global themes set the same wallpaper for the lock screen.

## [0.5.8] - 2026-11-21

Plymouth boot splash. Patch version (phase 5 is still in progress).

### Added

- `arctiva-branding` 0.5.0: Plymouth themes `arctiva` (the firmware vendor logo, BGRT, with the arc of Arctiva's ring spinning below) and `arctiva-logo` (centred Arctiva logo, for computers without a vendor logo).
- `arctiva-settings` 0.5.0: depends on `plymouth` and adds the `plymouth` hook to the installed system's initramfs, right after `udev` (not to the live one).

### Changed

- The installer picks the Plymouth theme by checking for the firmware logo (`/sys/firmware/acpi/bgrt/image`) and adds `splash` to the kernel command line.

## [0.5.7] - 2026-11-21

GRUB theme, always visible. Patch version (phase 5 is still in progress).

### Added

- `arctiva-branding` 0.4.0: "Arctiva" GRUB theme (dark "Orbit" background, logo, Outfit font, translucent blue selection, icons for Arctiva and other systems), generated at build time by `branding/grub/build-theme.sh`.
- `arctiva-settings` 0.4.0: `arctiva-grub-theme.hook` refreshes `/boot/grub/themes/arctiva` when `arctiva-branding` is installed or upgraded.

### Changed

- The installer copies the theme to `/boot/grub/themes/arctiva` without holes (`prepare-target`) and sets `GRUB_THEME`, `GRUB_GFXMODE=auto` and `GRUB_TIMEOUT_STYLE=menu`: the menu is always visible for 5 seconds.

## [0.5.6] - 2026-11-21

"Personalization" module in Arctiva Center. Patch version (phase 5 is still in progress).

### Added

- Arctiva Center 0.7.0: "Personalization" page after Welcome: light, dark or automatic mode, accent colour, wallpaper (Arctiva's or any image), centred or left-aligned taskbar and floating bar, text size, display scale and night light. "Restore the Arctiva look" (with confirmation) and "Advanced settings" (KDE System Settings). Everything runs as the user, without the helper.
- `arctiva-branding` 0.3.1: "Arctiva Dark" global theme variant, used by the automatic mode.

## [0.5.5] - 2026-11-21

Global theme and Windows-style desktop. Patch version.

### Added

- `arctiva-branding` 0.3.0: "Arctiva" global theme (`org.arctiva.desktop`) with a bottom taskbar from edge to edge, centred application icons, start menu with search, tray, clock and "Show desktop", Arctiva light colour scheme and a splash screen with the logo.
- `arctiva-settings` 0.3.0: new users start with that theme (`/etc/xdg/kdeglobals`, `/etc/xdg/ksplashrc`); existing users do not change.

## [0.5.4] - 2026-11-21

"Orbit" wallpapers. Patch version.

### Added

- `arctiva-branding` 0.2.0 installs the "Arctiva" wallpaper (`/usr/share/wallpapers/Arctiva`) in light and dark versions, generated at build time from the SVGs in `branding/wallpapers/` (1920x1080, 2560x1440, 3840x2160 and 1920x1200).

## [0.5.3] - 2026-11-21

Corporate typeface and logo tagline as paths. Patch version.

### Added

- `branding/fonts/`: Outfit (SIL OFL 1.1) with its licence.

### Changed

- The tagline of `arctiva-logo.svg` is now paths drawn with Outfit Light; the file has no live text.

## [0.5.2] - 2026-11-21

Snapshot limits. Patch version.

### Changed

- Snapper keeps at most 10 snapshots (5 of the important ones) and `snapper-cleanup.timer` removes the oldest; no space limit, as it needs Btrfs quotas.
- Arctiva Center shows the number of snapshots and the free disk space in the welcome page.

## [0.5.1] - 2026-11-21

Visual direction for phase 5 decided (step 5.0). Documentation only; patch version.

### Changed

- Architecture (D-13): Outfit as the corporate typeface, the "Orbit" wallpaper, light mode by default with Arctiva's own colour scheme and Breeze Dark with Arctiva's accent in dark mode, a full-width taskbar with a floating option, the ring arc as the boot indicator, and GRUB for the live ISO.

## [0.5.0] - 2026-11-21

Phase 4 closed: Arctiva Center (welcome, updates, drivers and extras). Closing tests passed on 2026-11-21: update from Arctiva Center, an extra, drivers with a simulated `lspci`, `.pacnew`, the GRUB hook with LUKS, and a fresh encrypted install with the 0.4.1 ISO that boots the default entry and the initial snapshot. No code changes. Minor version (phase completed, D-16).

## [0.4.1] - 2026-11-21

Boot fix after installing, found during the phase 4 closing tests. Patch version.

### Fixed

- The installed system could fail to boot GRUB's default entry (`error: premature end of file /@/boot/vmlinuz-linux`, then `you need to load the kernel first`): copying the system with `rsync -S` left the kernel's trailing zeros as a hole in Btrfs, and GRUB read it as the end of the file. The kernel is now copied without holes, also in `/usr/lib/modules`, from where mkinitcpio copies it again when it is upgraded. It showed up in an encrypted install, but it could also happen without encryption. The LTS kernel was not affected.
- Arctiva Center 0.6.2: the pacman log in Updates, Extras and Drivers, and the `.pacnew` diff, were cut at the height of their box and could not be scrolled. They now have a scroll bar, and the log follows the last line while it runs.

### Changed

- Roadmap: the visual identity and a simple, Windows-like desktop become phase 5 (0.6.0), ahead of the store, which moves to phase 6 (0.7.0). Phase 5 adds a "Personalisation" module in Arctiva Center with the basic settings and "Restore Arctiva's look", an always-visible themed GRUB menu, and snapshot limits. Steam, Proton and Heroic testing on real hardware moves to phase 7.
- `build.sh` accepts extra Arch Linux Archive mirrors for the same pinned date (`ARCHIVE_MIRRORS` variable, never mixed with current mirrors) and checks, with retries, that one responds before building, failing early with a clear message.

## [0.4.0] - 2026-11-21

Phase 3 closed: the installed system uses the signed `[arctiva]` repository. Tested with a full install of the 0.3.17 ISO in QEMU (UEFI, online, Gaming profile): `pacman -Sy` downloads and validates `arctiva.db`, the five in-house packages come from `[arctiva]`, the signing key has full trust, and `os-release`, zram, `reflector.timer`, multilib, the Gaming packages, the LTS kernel in GRUB and the initial snapshot are in place. The installer runs `/usr/lib/arctiva/install-drivers`. Idle after login, the system uses about 1.2 GB of RAM. Minor version (phase completed, D-16).

### Fixed

- The installed system's panel showed a blank icon: the Discover launcher, which the installer removes. A Plasma update script replaces it with Arctiva Center the first time the user logs in; on the live ISO, which has Discover, it does nothing (`arctiva-center` 0.6.1).

## [0.3.17] - 2026-11-21

GRUB kept in sync on upgrades (phase 4, step 4.7). Patch release.

### Added

- `arctiva-settings` 0.2.0: pacman hook `arctiva-grub.hook` and `/usr/lib/arctiva/update-grub`. When the `grub` package is upgraded, GRUB is reinstalled on the EFI partition (`EFI/arctiva`) and `grub.cfg` is regenerated. The `EFI/Boot/BOOTX64.EFI` fallback copy is updated only if it is Arctiva's (another one, such as Windows', is left alone). If `grub-install` fails, `grub.cfg` is not regenerated and a clear message asks not to restart. Nothing happens on BIOS systems, without the EFI partition mounted or without `EFI/arctiva`.
- `tests/update-grub-test.sh` (8 cases).

## [0.3.16] - 2026-11-21

Arctiva Center welcome (phase 4, step 4.6). Patch release.

### Added

- Welcome page: logo and version, the state of the graphics drivers, updates and extras with a button to each module, and how to go back to a snapshot from the GRUB menu. It opens when logging in (`/etc/xdg/autostart/arctiva-center-welcome.desktop`) until "Show this welcome when logging in" is unticked; it never opens by itself on the live ISO.
- On the live ISO, Arctiva Center shows a notice and its install and update actions are disabled.
- `arctiva-center` 0.6.0.

## [0.3.15] - 2026-11-21

Arctiva Center "Extras" module (phase 4, step 4.5). Patch release.

### Added

- Extras module: Gaming, Office and LTS kernel, each with a switch to install or remove it. Gaming and Office have the same packages as the installer profiles (a test fails if they diverge). The LTS kernel also installs the matching NVIDIA module when needed and updates the GRUB menu when it is installed or removed. Printing and the firewall are already in the base system: the module links to their System Settings pages.
- Helper: when removing an extra, packages still used by another installed extra are kept (for example, fonts shared by Gaming and Office); `remove_also` and `update_grub` in the catalogue.
- `arctiva-center` 0.5.0.

### Fixed

- Helper: removing an extra failed because the dry run used `pacman -Rns --print`, a combination pacman rejects; it now uses `-Rs --print`.

## [0.3.14] - 2026-11-21

Arctiva Center "Drivers" module (phase 4, step 4.4). Patch release.

### Added

- Drivers module: detected graphics cards, the drivers they need and whether they are installed, with an "Install drivers" button (helper operation `drivers-apply`); for older NVIDIA cards (GTX 10/900 and earlier), an explanation of why the free nouveau driver is used and what the AUR option involves.
- `tests/install-drivers-test.sh`: `install-drivers --upgrade` with fake `pacman`, `systemctl` and `mkinitcpio`.
- `arctiva-hardware` 0.2.0 and `arctiva-center` 0.4.0.

### Changed

- `install-drivers` moves from the installer to `arctiva-hardware` (`/usr/lib/arctiva/install-drivers`), shared by the installer and Arctiva Center. New `--upgrade` mode for the running system: `pacman -Syu --needed`, services enabled immediately, `mkinitcpio -P` at the end and an error code when something fails (architecture, D-10).

## [0.3.13] - 2026-11-21

Lower requirements. Patch release.

### Changed

- Disk: 25 GB minimum (40 GB recommended); the installer now asks for 25 GiB, which also lets "Install alongside" work on smaller disks. The base system takes about 5 GB.
- Installation media: a 4 GB USB stick is enough (the ISO takes 1.76 GiB).
- RAM stays at 4 GB (8 GB recommended) until it is measured on an installed system.

## [0.3.12] - 2026-11-21

Arctiva Center "Updates" module (phase 4, step 4.3). Patch release.

### Added

- Updates module: list from `checkupdates` with sensitive packages marked (`delicate.toml`); Arch Linux news published since the last completed full upgrade, where a news item requiring manual intervention blocks updating until it is marked as read; update with the real log; translated explanation of common pacman errors (`errors.toml`: locked database, no disk space, PGP signatures, conflicting files, broken dependencies, network) with a "Update the keyring first" or "Try again" action; Flatpak update afterwards; pending `.pacnew` files with their diff and "Keep mine" / "Use the new one"; restart recommended when the kernel, NVIDIA, Mesa, systemd or glibc changed.
- Update reminder: user timer `arctiva-center-check.timer` (15 minutes after logging in, then every 6 hours) running `arctiva-center --check`, which shows a notification with a button that opens the module, only for updates not in the previous notice. It does not run on the live ISO.
- `arctiva-center` 0.3.0.

### Changed

- The helper runs pacman with English messages so that errors can be recognised in any language (architecture, D-08).

## [0.3.11] - 2026-11-21

Arctiva Center privileged helper (phase 4, step 4.2). Patch release.

### Added

- `arctiva-helper`, run through `pkexec` with the polkit action `org.arctiva.center.helper` (`auth_admin_keep`, active sessions only). It accepts a closed set of operations (`update`, `extra-install`, `extra-remove`, `drivers-apply`, `pacnew-keep`, `pacnew-use`) and never package names or commands: packages and services come from its own catalogue, `.pacnew` paths must be regular files under `/etc` without links, and anything else exits with code 64 without running anything. It refuses to run while the pacman database is locked.
- Arctiva Center launches the helper without a shell and shows its output line by line; the window cannot be closed while it runs. The Updates page gets a provisional "Update the system" button.
- Tests for the helper with fake `pacman` and `systemctl`, including trap paths and invalid identifiers.
- `arctiva-center` 0.2.0.

### Changed

- The repository is now public; architecture (D-01) and roadmap updated.

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
