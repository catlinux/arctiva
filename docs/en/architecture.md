# Arctiva architecture

> **Status:** approved (version 0.1.7).
> Versión en castellano: [../es/arquitectura.md](../es/arquitectura.md)

This document analyses the project's feasibility and records the architecture decisions (D-01…D-16) with their rationale. Each approved decision will be marked **Approved**; decisions that change are rewritten here, and the change is recorded in the CHANGELOG.

## 1. Feasibility

The goal is feasible and has precedents. EndeavourOS (official Arch repositories plus a small repository of its own, Calamares installer), CachyOS, Garuda Linux and SteamOS 3 (Valve) show that an Arch-based distribution can offer a graphical installer and a good gaming experience. There are also cautionary examples: Manjaro maintains its own delayed repositories, which causes incompatibilities with the AUR, and several single-maintainer projects have shut down because of the maintenance load.

Conclusion: **realistic as long as the in-house code stays small** and almost everything is integration and configuration of mature components. The main risk is not technical but the ongoing maintenance of a rolling-release project run by few people.

What is **not** realistic and will not be promised:

- Universal compatibility with Windows software and games (see D-12).
- A rolling release that never breaks. Snapshots, a fallback LTS kernel and warnings mitigate this, but users must be able to see problems.
- Secure Boot enabled out of the box in 1.0 (see D-05).

## 2. Initial ideas worth correcting

| Initial idea | Problem | Proposal |
|---|---|---|
| "No own repositories" | The installer (Calamares is not in the official repositories), the branding and the in-house tools need a channel to reach and update users. | A **minimal, signed** repository (`[arctiva]`) containing only our own packages and the essentials that Arch does not ship. It never contains modified official packages (D-01). |
| AUR inside the store | The AUR is unreviewed: anyone can publish scripts that run with build permissions. For users coming from Windows this is a security risk. | Accepted with conditions: a separate, clearly visible source, disabled until the user enables it, a warning before every installation and a viewable PKGBUILD (D-07). |
| A store mixing pacman, AUR and Flatpak | On Arch, Discover with PackageKit works poorly: the ArchWiki advises against using PackageKit front-ends to upgrade, and KDE calls Arch support very poor. Background database refreshes can cause partial upgrades, which Arch does not support. | An in-house store, inside Arctiva Center, that keeps the three sources apart and never leaves the system partially upgraded (D-07). |
| A complete ISO on GitHub | GitHub Releases requires each file to be under 2 GiB. | An ISO under 2 GiB with the full desktop, with extras downloaded during installation; fallback to an external mirror (D-14). |

## 3. Architecture decisions

### D-01 Base: unmodified Arch plus a minimal own repository (**Approved**)

- Official `core`, `extra` and `multilib` repositories, unchanged and without delays. Pacman remains the only system package manager.
- A GPG-signed `[arctiva]` repository with only what the installed system uses: `arctiva-keyring`, `arctiva-settings`, `arctiva-branding`, `arctiva-hardware` and, later, `arctiva-center`. It is hosted in a separate public repository (`catlinux/arctiva-repo`) as the files of a fixed release, so an installed system downloads only the packages, not the source code. How it is signed: [signing.md](signing.md).
- `calamares`, `ckbcomp` and the installer configuration are only useful on the ISO: they are built locally for every build (against the ISO's Archive date) and removed from the installed system.
- `/etc/os-release` belongs to the `filesystem` package, which is not repackaged: `arctiva-settings` ships a pacman hook that rewrites it after every `filesystem` update.
- Forbidden: repackaging or holding back official packages. If an official package breaks, the response is warnings and snapshots, not a fork.

### D-02 ISO build: archiso (**Approved**)

- `archiso` is the official tool Arch uses to build its own ISO. The Arctiva profile derives from the `releng` profile.
- **Reproducibility:** each release pins a date of the Arch Linux Archive (`archive.archlinux.org/repos/YYYY/MM/DD`), so a given ISO can be rebuilt with the same packages. The build script and the pinned date are versioned.

### D-03 Installer: a tailored Calamares (**Approved**)

- Alternatives considered: **archinstall** (official but text-only), **Anaconda** (tied to Fedora), the Ubuntu, elementary/Pop!_OS and Vanilla OS installers (each tied to its distribution) and **an in-house installer** (huge cost; partitioning, especially resizing Windows for dual boot, is where data loss is most likely).
- **Calamares** is the engine: mature, Qt-based (a good fit with KDE), modular, used by EndeavourOS, Manjaro, KaOS, Debian live and others. It covers language, keyboard, time zone, users, manual and automatic partitioning, installing alongside Windows, UEFI and LUKS encryption.
- **Its plain look is the default configuration, not a limitation.** The interface is rebuilt in QML so that it carries the Arctiva identity:
  - Custom QML sidebar and navigation (`sidebar: qml` and `navigation: qml` in the branding).
  - QML versions of the pages Calamares ships (`welcomeq`, `localeq`, `keyboardq`, `usersq`, `summaryq`, `finishedq`) with our own design. The profile (Basic, Gaming, Office; the last two are downloaded when a connection is available) is chosen with the widget `packagechooser` in `optionalmultiple` mode (`packagechooserq` only allows one choice and `netinstall` lets users pick single packages); Basic is what the ISO carries and is always installed, and the "Check" page (see dual boot) uses `notesqml`.
  - Page order: welcome, language and region, keyboard, profile, check, disk, users, summary, installation and finish.
  - The partitioning page has no QML version: it is integrated through a Qt stylesheet (`stylesheet.qss`) so it follows the same design. If some part drawn in C++ (the partition bar) ignores it, it is left as is.
  - Identity: sidebar with the logo's night-blue gradient, light content with a blue accent, and warnings shown with an icon and text, never colour alone. Noto Sans as a provisional typeface until the corporate one is chosen.
  - A QML slideshow while files are copied.
  - **No patches to Calamares' C++ code**: only configuration, branding and our own modules (QML or Python). If a patch is ever needed, it is proposed upstream.
- If the result fell short, the alternative would be a custom interface on top of the archinstall engine, solving Windows partition resizing separately. It would be assessed with a prototype.
- Install mode: **offline**, copying the already tested live system (`unpackfs` module) and removing live-only bits. Then **optional online extras** (gaming, office…) through the `netinstall` module when a connection is available. This is fast, works without a network, and what gets installed is what was tested.
- **Dual boot with Windows:** many Windows 11 machines ship with the partition encrypted by BitLocker (device encryption). Calamares cannot resize an encrypted partition, and it does not detect BitLocker or Windows Fast Startup, which leaves NTFS in a hibernated state. Our own launcher runs before Calamares and checks the machine (BitLocker partitions, hibernated NTFS through `ntfs-3g.probe`, presence of Windows); the "Check" page, before the disk page, shows the result:
  - **Block:** Windows is hibernated or uses Fast Startup. The page explains how to shut it down fully and offers to quit the installer; installing alongside Windows is not possible until that is fixed (`ntfsresize`, from the `ntfsprogs` package, refuses to shrink a hibernated NTFS). Calamares does not let a QML page disable "Next", so the block is a recommendation and does not prevent erasing the whole disk.
  - **Warning:** BitLocker is on. Shrink the partition from Windows (Disk Management) and keep the recovery key at hand, as Windows will ask for it after Secure Boot was changed (D-05).
  - GRUB lists Windows in its menu (`os-prober`). Arctiva keeps the firmware clock in UTC and Windows in local time: the help explains how to align them.
- Risk: Calamares is not in the official repositories. It is built into `[arctiva]` and its releases are tracked (3.4.3, from September 2026, is the pinned one; it builds with Qt 6). Its QML API changes between releases, so the version is pinned in our repository and every update is tested before release.

### D-04 Disk, boot and recovery (**Approved**)

- **UEFI with GPT only** in 1.0: every PC that runs Windows 10/11 has it, and it halves the test matrix. Legacy BIOS is out for now. The ISO only boots in UEFI mode, so a machine without UEFI never reaches the installer (Calamares does not check the boot mode).
- **EFI partition** mounted at `/boot/efi`; it only holds GRUB, so the Windows one can be reused. **`/boot` lives inside `@`**: every snapshot keeps the kernel and initramfs that match its modules and boots without mismatches.
- **Btrfs** with subvolumes (`@`, `@home`, `@cache`, `@log`, `@snapshots`) and zstd compression. `@snapshots` is mounted at `/.snapshots`, outside `@`: without it, Snapper cannot roll the system back to an earlier snapshot.
- **Snapper + snap-pac**: automatic snapshots before and after every pacman transaction.
- **GRUB + grub-btrfs**: snapshots can be booted from the menu, which is the recovery path after a failed upgrade. Snapshots are read-only: the `grub-btrfs-overlayfs` mkinitcpio hook adds a temporary writable layer on top so they can boot. systemd-boot cannot boot snapshots; Limine can, but its integrations live in the AUR. Everything chosen is in the official repositories.
- **Kernels:** `linux` (default) and `linux-lts` as a fallback entry. `linux-lts` is not on the ISO (it would take about 250 MB, D-14): the installer downloads it when a connection is available, and otherwise Arctiva Center offers it later.
- **Swap:** zram (`zram-generator`). zram does not allow hibernation: 1.0 has no hibernation (suspend works). Adding it later (an `@swap` subvolume with a swap file) is pending.
- **Encryption (optional, off by default):** **LUKS1** on the Arctiva partition, with `/boot` encrypted inside it. GRUB asks for the passphrase **only once**; a key file inside the initramfs, which lives on the encrypted partition, unlocks the system without asking again (`luksbootkeyfile` and `initcpiocfg` modules with the `encrypt` hook, which is also the one `grub-btrfs-overlayfs` needs).
  - Why not LUKS2: GRUB supports Argon2 since 2.14 (Arch ships 2.16), but Calamares does not let us choose the key derivation function and uses Argon2id with 1 GiB of memory, which has been reported to leave GRUB out of memory at boot. LUKS1 is Calamares' default and the best-tested path.
  - When encryption is ticked, the installer warns that the passphrase is typed at boot with the **US keyboard layout** (better to use letters without accents and digits) and that without it the data cannot be recovered.
  - Later: LUKS2 to unlock with TPM2 or FIDO2, once Calamares lets us choose the function or through a conversion from the live USB.

### D-05 Secure Boot (**Approved**)

Arch does not provide Secure Boot out of the box (the signed `shim` is in the AUR). In 1.0, users will have to disable it, and the documentation and installer will explain how. `sbctl` with custom keys will be studied later. This is a real barrier for people coming from Windows 11, and it is documented as such. On a machine with BitLocker, changing Secure Boot makes Windows ask for the recovery key on the next boot: users are warned beforehand and told where to find it.

### D-06 Desktop: KDE Plasma 6 on Wayland (**Approved**)

- Considered: **GNOME** (a paradigm far from Windows, and extensions that break with every release), **Cinnamon** (very Windows-like, but its Wayland support is still immature), **COSMIC** (promising but still young), **Xfce** (still on X11).
- **Plasma**: Windows-like layout by default (menu, taskbar, system tray), complete graphical settings, Dolphin, good VRR/HDR support, good for gaming and laptops, and global themes (Look-and-Feel) that provide an identity **without patching KDE**.
- Customisation only through configuration packages (`/etc/xdg`, `/etc/skel`, global theme), so a Plasma update does not break anything of ours.
- Wayland session only: since Plasma 6.8, KDE no longer ships an X11 session. X11 applications keep working through Xwayland.
- Login manager: **Plasma Login Manager** (KDE's official one, in `extra`; Calamares 3.4 can already configure it). Its Breeze look is fixed, so the identity is limited to the wallpaper and colours. Fallback: SDDM with a custom theme if the former falls short.

### D-07 Applications: store and sources (**Approved**)

Requirements:

- A graphical store to search, install, update and remove software from **three sources**: the official repositories (pacman), Flathub (Flatpak) and the AUR.
- The origin of every application is always visible, with a distinct badge per source. If an application exists in several sources, they are shown as separate options with one marked as recommended.
- **AUR:** disabled by default. When enabling it, and before every installation, a clear warning that it is unreviewed community software, with a viewable PKGBUILD. Packages are built without root through a helper (`paru`) from `[arctiva]`.
- **pacman integrity:** no operation refreshes the databases without upgrading the whole system. Installing a repository package on an outdated system requires upgrading first.
- Flatpak permissions visible and adjustable. Understandable errors, with the original text available.

Decision: **an in-house store as the "Applications" module of Arctiva Center** (D-09). The installed system does not ship Discover, to avoid two stores and PackageKit's periodic refresh. The live ISO uses Discover with Flathub only until phase 5.

- **Catalogue:** AppStream data from the repositories (`archlinux-appstream-data`) and from Flathub, read with libappstream. An application available from several sources is shown once, with one option per source. The AUR only appears when enabled, as a list of packages searched through its RPC API.
- **Recommended source:** the official repositories before Flathub, except for the exceptions set in `arctiva-settings` (for example Bottles, D-12). The AUR is never the recommended one.
- **pacman:** queries use `pyalpm` on a temporary copy of the databases, like `checkupdates`; the real database is never touched outside an upgrade. Installing is `pacman -Syu --needed <packages>` through the polkit helper; if updates are pending, the D-08 flow (news, snapshot, sensitive packages) runs first.
- **Flatpak:** libflatpak, or the `flatpak` command if the proof of concept advises it. Permissions are managed by opening `flatpak-kcm`, the existing Plasma module.
- **AUR:** before installing, the full PKGBUILD and `.install`, votes, popularity, last update and maintainer are shown, with a stronger warning if the package is orphaned, has changed maintainer or is recent. On every update, a diff of the PKGBUILD and `.install` against the installed version, with confirmation: in June 2026 Arch warned of a wave of malicious AUR packages and advised reviewing all changes. Packages are built as the user with `paru`; only installing the built package goes through the helper. AUR updates run after `pacman -Syu`.
- **Errors:** the same message translator as D-08.
- Rejected: Discover's PackageKit back-end, because of the risk of partial upgrades (section 2); Discover with a custom back-end for pacman and the AUR (none exists and Discover's back-end interface is not stable, so C++ code would have to keep pace with Plasma); Pamac (AUR only, tied to Manjaro and GTK); Bauh (no development since 2024, Qt5); and Octopi (a package manager without Flatpak or AppStream).
- Before phase 5, a proof of concept in the VM validates the catalogue, the temporary-database queries, installation through the helper, Flatpak and the AUR flow. The decision will be reconsidered if KDE adds a pacman back-end to Discover.

### D-08 Updates (**Approved**)

In the Arctiva Center update module:

1. Detect updates with `checkupdates` (pacman-contrib), which uses a temporary database and cannot cause partial upgrades.
2. Show the archlinux.org news published since the last upgrade. If an item requires manual intervention, the process stops until the user has read it, with the explanation and the concrete action.
3. List the packages and highlight the sensitive ones (kernel, NVIDIA drivers, Mesa, systemd, Plasma).
4. Upgrade with `pacman -Syu` through a privileged helper (polkit), showing the real log. snap-pac takes the snapshot beforehand.
5. Update Flatpaks.
6. Report `.pacnew` files and recommend a reboot if the kernel or drivers changed.
7. Translate common errors (conflicts, PGP keys, disk space) into understandable messages without hiding the original text. The helper runs pacman with English messages (`LC_ALL=C.UTF-8`) so that errors are recognised whatever the user's language; the explanation is shown translated and the original log stays one click away.

News count from the last full upgrade that completed a transaction in `/var/log/pacman.log` (pacman also logs the start of upgrades that fail, and those must not hide news). A user timer (`arctiva-center-check.timer`, 15 minutes after logging in and then every 6 hours) runs `arctiva-center --check`, which notifies only when there are updates that were not in the previous notice.

**arch-update evaluation (2026-11-21):** it is not used as a dependency. It is AUR-only (4.4.7), a terminal and tray tool built with `cargo` and `scdoc` that depends on `htmlq`, `archlinux-contrib` and `fakeroot`, and its interface does not fit Arctiva Center. What it provides (`checkupdates`, the archlinux.org RSS news and `pacdiff`) is used directly, and only what is missing gets written. `checkupdates` needs `fakeroot`, which `pacman-contrib` does not declare: `arctiva-center` depends on it explicitly.

### D-09 In-house tools: a single application (**Approved**)

**Arctiva Center**, in Python 3 + PySide6 (Qt 6, both in the official repositories), with `pyalpm` for read-only queries. Modules: first-boot welcome, drivers, updates, extras (catalogue) and applications (the store, D-07). The helper, the error translator and the update flow are shared by all modules. Privileged actions go through a polkit helper exposing a **closed set of operations**, never arbitrary commands. One application instead of several keeps maintenance down.

Design (phase 4): the interface in QML with Kirigami, so it looks like the rest of Plasma, and the logic in Python without Qt, so it can be tested. The helper is a single script run through `pkexec` that only accepts identifiers from its own catalogue (update, install or remove an extra, apply drivers, resolve a `.pacnew`), never package names or commands. A user timer reports updates every 6 hours. A hook in `arctiva-settings` reinstalls GRUB on the EFI partition when the `grub` package is upgraded.

### D-10 Graphics (**Approved**)

Detection with `lspci` and a mapping file (family → packages), shared by the installer and Arctiva Center.

| GPU | Packages |
|---|---|
| AMD Radeon (GCN and newer) | `mesa`, `vulkan-radeon`, `lib32-mesa`, `lib32-vulkan-radeon` |
| Intel integrated and Arc | `mesa`, `vulkan-intel`, `intel-media-driver`, `lib32` variants |
| NVIDIA Turing and newer (GTX 16, RTX 20+; PCI device id `>= 0x1E00`) | `nvidia-open` and `nvidia-open-lts` (prebuilt modules for both kernels), `nvidia-utils`, `lib32-nvidia-utils`, early KMS |
| NVIDIA Pascal/Maxwell (GTX 10/900) | Since December 2025 the 580xx driver is only in the AUR. **Not installed automatically**: `nouveau` is used and the user is told the options |
| Hybrid laptops | `switcheroo-control` and Plasma integration to launch on the dedicated GPU |

### D-11 Gaming (**Approved**)

- `multilib` enabled by default, also on the installed system (`prepare-target` enables it).
- Native Steam (`steam`, from multilib), `gamemode`, `mangohud`, `gamescope`; Proton is managed from Steam.
- Heroic (Epic/GOG) and ProtonPlus or ProtonUp-Qt as Flatpaks; Lutris from `extra`.
- Installed as a "Gaming" profile during installation (Steam, Lutris, GameMode, MangoHud, Gamescope and the 32-bit Mesa and Vulkan libraries) or from Arctiva Center. Heroic, ProtonPlus and Bottles will be offered by Arctiva Center (phase 5); NVIDIA drivers, by GPU detection (phase 3).

### D-12 Windows software (**Approved**)

- **Bottles** as the main tool, **Flatpak only**: it is the only format its developers support.
- Opening an `.exe` or `.msi` shows our own dialog that explains what will happen, offers to open it with Bottles and links to the compatibility databases (WineHQ AppDB, ProtonDB).
- Limitations that are communicated clearly: games with kernel-level anti-cheat (see "Are We Anti-Cheat Yet?"), suites such as recent Adobe and Microsoft Office, Windows drivers and hardware utilities.
- `wine` and `winetricks` from the repositories, for advanced users.

### D-13 Identity and trademark (**Approved**)

- Name: **Arctiva** (formerly "Archtiva"). It no longer contains the "Arch" mark. Arch's trademark policy allows describing it as "based on Arch Linux"; it will never present itself as official.
- No distribution or software with this name has been found. There is a registered US trademark "ARCTIVA" in class 5 (pharmaceuticals), which is distinct from software (class 9). Low risk; to be reviewed before 1.0.
- Our own vector logo in `branding/logo/`: an open arch, like a gateway without barriers, crossed by a glowing orbit. Its rounded shape is distinct from the peak of the Arch logo. Colour, monochrome and app-icon variants are provided.
- The name and logo are not covered by the code licence: their use is governed by [TRADEMARKS.md](../../TRADEMARKS.md).
- Arch does not support derivatives: Arctiva will have its own help channels and will never send users to the Arch forums.

### D-14 ISO distribution (**Approved**)

GitHub Releases accepts files **under 2 GiB** each, with no limit on total size or bandwidth. Options considered:

| Option | Assessment |
|---|---|
| Full ISO over 2 GiB on GitHub | Impossible |
| Split the ISO into parts | Rejected: Rufus, Ventoy and Etcher need a single file; a poor experience for Windows users |
| Minimal network ISO that downloads everything | Rejected as the main option: users cannot try the desktop without installing, and it depends on the network and mirror state |
| **ISO under 2 GiB with the full desktop, extras downloaded during installation** | **Recommended** |
| External mirror (SourceForge or own server) | Fallback if the ISO exceeds the limit; GitHub keeps the checksums and signature |

To stay under 2 GiB: a selection of Plasma packages instead of every meta-package, xz compression of the filesystem, and Steam, office and gaming as online profiles at install time. CI will fail if the ISO grows beyond 1.9 GiB.

**Measured on 2026-11-20** (packages from 2026-11-19): with `linux-lts` and package documentation the ISO took 2.12 GiB. Without them it takes **1.75 GiB**. The largest parts: firmware (about 500 MB that is already compressed), Firefox, `qt6-webengine` (required by Discover and the KDE applications) and translations (about 480 MB uncompressed, all of them kept). If it gets close to the limit again, the next candidate is limiting the translations on the ISO.

### D-15 Automation (GitHub Actions) (**Approved**)

1. **Lint:** shellcheck, `namcap` for PKGBUILDs and a link check for the documentation.
2. **Packages:** built in a clean Arch container and signed.
3. **ISO:** `mkarchiso` in a privileged `archlinux` container. The standard runner leaves about 14 GB free, which is tight for the build: if it is not enough, the unused preinstalled tools are removed first.
4. **Boot test:** headless QEMU/KVM with UEFI firmware (OVMF), checking over the serial console that the desktop is reached. Automated installation later.
5. **Scheduled weekly build** with the current packages, to detect Arch breakage before users do. GitHub disables scheduled workflows in a public repository after 60 days without activity: if that happens, it has to be re-enabled.
6. **Release** only from an approved tag: ISO, `sha256`, GPG signature and release notes generated from the CHANGELOG.

### D-16 Versioning (**Approved**)

- The project follows SemVer `x.y.z` (`VERSION` file). Each published ISO carries the project version: `arctiva-X.Y.Z-x86_64.iso`.
- Before 1.0: each completed phase bumps the minor version; fixes and documentation bump the patch.
- From 1.0: major when users must migrate (for example, a different subvolume layout), minor when features are added, patch for fixes or rebuilds.
- Each `[arctiva]` package has its own `pkgver` in its PKGBUILD.

## 4. What we build and what we integrate

| In-house (small) | Integrated, no own code |
|---|---|
| archiso profile and build scripts | Arch Linux (core, extra, multilib), pacman |
| Calamares QML interface, configuration and branding | Calamares, KDE Plasma, Discover (live only), Flatpak/Flathub |
| Store: the "Applications" module of Arctiva Center (D-07) | pyalpm, paru, libflatpak, AppStream, flatpak-kcm |
| `arctiva-settings` (defaults) | Btrfs, Snapper, snap-pac, grub-btrfs, zram-generator |
| `arctiva-branding` (logo, wallpapers, Plymouth, global theme) | Mesa, NVIDIA open, Vulkan, firmware, fwupd |
| `arctiva-keyring` and the `[arctiva]` repository | Steam, Proton, Lutris, Heroic, Bottles, gamemode, MangoHud |
| Arctiva Center (welcome, drivers, updates, extras) | reflector, pacman-contrib, CUPS, ufw + plasma-firewall |
| GitHub Actions workflows and tests | `checkupdates`, RSS and `pacdiff` (arch-update evaluated and rejected as a dependency) |

## 5. Main risks

| Risk | Impact | Mitigation |
|---|---|---|
| Arch breakage (e.g. the NVIDIA 590 change) | High | Weekly CI builds, blocking news, snapshots, LTS kernel |
| Single maintainer | High | Little in-house code, everything documented and automated |
| Calamares or KDE changes | Medium | Configuration only, versions tracked in CI |
| Secure Boot required on some machines | Medium | Clear documentation; `sbctl` later |
| Windows with BitLocker in dual boot | High | Warnings in the installer and documentation: recovery key at hand, shrink the partition from Windows, Fast Startup off |
| ISO over 2 GiB | Medium | Package selection and an external mirror |
| Name and logo versus other trademarks | Low | Name without "Arch", own logo, review before 1.0 |
| AUR security | Medium | Disabled by default, kept separate, with warnings and a PKGBUILD diff on every update |
| Cost of building the in-house store | Medium | Shares the helper, the error translator and the D-08 flow; proof of concept before phase 5 |
| Repository signing keys | High | Offline primary key; signing subkey in Actions secrets ([guide](signing.md)) |
| VirtualBox tests not representative (3D, Wayland) | Medium | Live-USB tests on real hardware before every release |

## 6. Hardware requirements

**Current host:** Intel i5-14400F (10 cores, 16 threads), 16 GB RAM, NVIDIA RTX 4060, 108 GB free on C:. Hyper-V is active, so VirtualBox runs on top of it: slower, and no nested virtualisation.

| Machine | CPU | RAM | Disk | Notes |
|---|---|---|---|---|
| Build VM (Arch Linux) | 4–6 vCPU | 8 GB | 80 GB dynamic | EFI. Builds packages and the ISO. The "Arctiva" VM is already set up with 4 vCPU, 8 GB and 80 GB (see [development.md](development.md)) |
| ISO test VM | 2–4 vCPU | 4 GB | 40 GB dynamic | EFI, VMSVGA with 128 MB video memory. Recreated for every test |
| Real hardware | — | — | USB stick of 8 GB or more | The host's RTX 4060 can be used to test NVIDIA from the live USB |
| GitHub Actions | standard runner | 16 GB | ~14 GB free | Enough for an ISO under 2 GiB |

**Arctiva minimum requirements (target):** x86-64 with UEFI, 4 GB RAM (8 GB recommended), 40 GB disk (64 GB recommended because of snapshots), and a Vulkan-capable GPU for gaming.
