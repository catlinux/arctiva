# Archtiva architecture

> **Status:** proposal pending approval (version 0.1.0).
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
| "No own repositories" | The installer (Calamares is not in the official repositories), the branding and the in-house tools need a channel to reach and update users. | A **minimal, signed** repository (`[archtiva]`) containing only our own packages and the essentials that Arch does not ship. It never contains modified official packages (D-01). |
| AUR inside the store | The AUR is unreviewed: anyone can publish scripts that run with build permissions. Putting it in a store for users coming from Windows is a security risk. | The AUR is an advanced option that users enable deliberately, with a warning, and it is never part of the store (D-07). |
| A store mixing pacman, AUR and Flatpak | On Arch, Discover with PackageKit works poorly: the ArchWiki advises against using PackageKit front-ends to upgrade, and KDE calls Arch support very poor. Background database refreshes can cause partial upgrades, which Arch does not support. | Store = Discover with Flatpak/Flathub and firmware only. System packages are installed from a curated catalogue in Archtiva Center that always upgrades the whole system (D-07). |
| A complete ISO on GitHub | GitHub Releases requires each file to be under 2 GiB. | An ISO under 2 GiB with the full desktop, with extras downloaded during installation; fallback to an external mirror (D-14). |

## 3. Architecture decisions

### D-01 Base: unmodified Arch plus a minimal own repository

- Official `core`, `extra` and `multilib` repositories, unchanged and without delays. Pacman remains the only system package manager.
- A GPG-signed `[archtiva]` repository hosted on GitHub, containing our own packages (`archtiva-settings`, `archtiva-branding`, `archtiva-keyring`, `archtiva-center`, Calamares configuration) and builds of the essentials that only exist in the AUR (`calamares`, `ckbcomp`).
- Forbidden: repackaging or holding back official packages. If an official package breaks, the response is warnings and snapshots, not a fork.

### D-02 ISO build: archiso

- `archiso` is the official tool Arch uses to build its own ISO. The Archtiva profile derives from the `releng` profile.
- **Reproducibility:** each release pins a date of the Arch Linux Archive (`archive.archlinux.org/repos/YYYY/MM/DD`), so a given ISO can be rebuilt with the same packages. The build script and the pinned date are versioned.

### D-03 Installer: Calamares

- Alternatives considered: **archinstall** (official but text-only), **Anaconda** (tied to Fedora), **an in-house installer** (huge cost and partitioning risk).
- **Calamares**: a mature Qt installer (a good fit with KDE), modular and brandable, used by EndeavourOS, Manjaro, KaOS, Debian live and others. It covers language, keyboard, time zone, users, manual and automatic partitioning, installing alongside Windows, UEFI and LUKS encryption.
- Install mode: **offline**, copying the already tested live system (`unpackfs` module) and removing live-only bits. Then **optional online extras** (gaming, office…) through the `netinstall` module when a connection is available. This is fast, works without a network, and what gets installed is what was tested.
- Risk: Calamares is not in the official repositories. It is built into `[archtiva]` and its releases are tracked (the 3.4 series is active in 2026).

### D-04 Disk, boot and recovery

- **UEFI with GPT only** in 1.0: every PC that runs Windows 10/11 has it, and it halves the test matrix. Legacy BIOS is out for now.
- **Btrfs** with subvolumes (`@`, `@home`, `@cache`, `@log`) and zstd compression.
- **Snapper + snap-pac**: automatic snapshots before and after every pacman transaction.
- **GRUB + grub-btrfs**: snapshots can be booted from the menu, which is the recovery path after a failed upgrade. systemd-boot cannot boot snapshots; Limine can, but its integrations live in the AUR. Everything chosen is in the official repositories.
- **Kernels:** `linux` (default) and `linux-lts` as a fallback entry.
- **Swap:** zram (`zram-generator`).

### D-05 Secure Boot

Arch does not provide Secure Boot out of the box (the signed `shim` is in the AUR). In 1.0, users will have to disable it, and the documentation and installer will explain how. `sbctl` with custom keys will be studied later. This is a real barrier for people coming from Windows 11, and it is documented as such.

### D-06 Desktop: KDE Plasma 6 on Wayland

- Considered: **GNOME** (a paradigm far from Windows, and extensions that break with every release), **Cinnamon** (very Windows-like, but its Wayland support is still immature), **COSMIC** (promising but still young), **Xfce** (still on X11).
- **Plasma**: Windows-like layout by default (menu, taskbar, system tray), complete graphical settings, Dolphin, good VRR/HDR support, good for gaming and laptops, and global themes (Look-and-Feel) that provide an identity **without patching KDE**.
- Customisation only through configuration packages (`/etc/xdg`, `/etc/skel`, global theme), so a Plasma update does not break anything of ours.
- Wayland session by default (KDE has announced that it is dropping Plasma's X11 session).
- Login manager: **Plasma Login Manager** (KDE's official one, in `extra`). Its Breeze look is fixed, so the identity is limited to the wallpaper and colours. Fallback: SDDM with a custom theme if the former falls short.

### D-07 Applications: store, catalogue and AUR

- **Store:** KDE Discover with the **Flatpak (Flathub)** and **fwupd** (firmware) back-ends only. Flathub is the default source of desktop applications: they are sandboxed, their permissions are visible and adjustable, and they update independently of the system. Discover shows the origin of every application.
- Discover's PackageKit back-end is **not installed** (see section 2).
- **System packages** (drivers, codecs, printing, Steam, gaming tools): a curated catalogue in Archtiva Center (D-09), installed with `pacman -Syu --needed <packages>` so the system is always up to date first, which avoids partial upgrades.
- **AUR:** an advanced option, disabled by default. It is enabled from Archtiva Center with a clear warning, which installs a helper (`paru`) from `[archtiva]`. It is never part of the store.

### D-08 Updates

In the Archtiva Center update module:

1. Detect updates with `checkupdates` (pacman-contrib), which uses a temporary database and cannot cause partial upgrades.
2. Show the archlinux.org news published since the last upgrade. If an item requires manual intervention, the process stops until the user has read it, with the explanation and the concrete action.
3. List the packages and highlight the sensitive ones (kernel, NVIDIA drivers, Mesa, systemd, Plasma).
4. Upgrade with `pacman -Syu` through a privileged helper (polkit), showing the real log. snap-pac takes the snapshot beforehand.
5. Update Flatpaks.
6. Report `.pacnew` files and recommend a reboot if the kernel or drivers changed.
7. Translate common errors (conflicts, PGP keys, disk space) into understandable messages without hiding the original text.

Before writing this logic, reusing **arch-update** will be evaluated (an AUR tool that already handles news, `.pacnew` files and Flatpak, maintained by an Arch packager). Only what is missing gets written.

### D-09 In-house tools: a single application

**Archtiva Center**, in Python 3 + PySide6 (Qt 6, both in the official repositories), with `pyalpm` for read-only queries. Modules: first-boot welcome, drivers, updates, extras (catalogue) and advanced options (AUR). Privileged actions go through a polkit helper exposing a **closed set of operations**, never arbitrary commands. One application instead of several keeps maintenance down.

### D-10 Graphics

Detection with `lspci` and a mapping file (family → packages), shared by the installer and Archtiva Center.

| GPU | Packages |
|---|---|
| AMD Radeon (GCN and newer) | `mesa`, `vulkan-radeon`, `lib32-mesa`, `lib32-vulkan-radeon` |
| Intel integrated and Arc | `mesa`, `vulkan-intel`, `intel-media-driver`, `lib32` variants |
| NVIDIA Turing and newer (GTX 16, RTX 20+) | `nvidia-open` and `nvidia-lts-open` (prebuilt modules for both kernels), `nvidia-utils`, `lib32-nvidia-utils`, early KMS |
| NVIDIA Pascal/Maxwell (GTX 10/900) | Since December 2025 the 580xx driver is only in the AUR. **Not installed automatically**: `nouveau` is used and the user is told the options |
| Hybrid laptops | `switcheroo-control` and Plasma integration to launch on the dedicated GPU |

### D-11 Gaming

- `multilib` enabled by default.
- Native Steam (`steam`, from multilib), `gamemode`, `mangohud`, `gamescope`; Proton is managed from Steam.
- Heroic (Epic/GOG) and ProtonPlus or ProtonUp-Qt as Flatpaks; Lutris from `extra`.
- Installed as a "Gaming" profile during installation or from Archtiva Center.

### D-12 Windows software

- **Bottles** as the main tool, **Flatpak only**: it is the only format its developers support.
- Opening an `.exe` or `.msi` shows our own dialog that explains what will happen, offers to open it with Bottles and links to the compatibility databases (WineHQ AppDB, ProtonDB).
- Limitations that are communicated clearly: games with kernel-level anti-cheat (see "Are We Anti-Cheat Yet?"), suites such as recent Adobe and Microsoft Office, Windows drivers and hardware utilities.
- `wine` and `winetricks` from the repositories, for advanced users.

### D-13 Identity and trademark

- Arch's trademark policy allows saying "based on Arch Linux" but not using its marks to name the product or implying that it is official. **Before publishing**, `trademarks@archlinux.org` will be asked whether the name "Archtiva" is acceptable.
- The logo must not resemble the Arch logo. The current draft (an "A" with an inner curve) is too close; it needs to move away from it and exist as vector art (SVG), with a monochrome variant for small icons and the boot splash.
- Arch does not support derivatives: Archtiva will have its own help channels and will never send users to the Arch forums.

### D-14 ISO distribution

GitHub Releases accepts files **under 2 GiB** each, with no limit on total size or bandwidth. Options considered:

| Option | Assessment |
|---|---|
| Full ISO over 2 GiB on GitHub | Impossible |
| Split the ISO into parts | Rejected: Rufus, Ventoy and Etcher need a single file; a poor experience for Windows users |
| Minimal network ISO that downloads everything | Rejected as the main option: users cannot try the desktop without installing, and it depends on the network and mirror state |
| **ISO under 2 GiB with the full desktop, extras downloaded during installation** | **Recommended** |
| External mirror (SourceForge or own server) | Fallback if the ISO exceeds the limit; GitHub keeps the checksums and signature |

To stay under 2 GiB: a selection of Plasma packages instead of every meta-package, xz compression of the filesystem, and Steam, office and gaming as online profiles at install time. CI will fail if the ISO grows beyond 1.9 GiB. **The real size will be measured in phase 1**; until then it is a target, not a fact.

### D-15 Automation (GitHub Actions)

1. **Lint:** shellcheck, `namcap` for PKGBUILDs and a link check for the documentation.
2. **Packages:** built in a clean Arch container and signed.
3. **ISO:** `mkarchiso` in a privileged `archlinux` container.
4. **Boot test:** headless QEMU/KVM with UEFI firmware (OVMF), checking over the serial console that the desktop is reached. Automated installation later.
5. **Scheduled weekly build** with the current packages, to detect Arch breakage before users do.
6. **Release** only from an approved tag: ISO, `sha256`, GPG signature and release notes generated from the CHANGELOG.

### D-16 Versioning

- The project follows SemVer `x.y.z` (`VERSION` file). Each published ISO carries the project version: `archtiva-X.Y.Z-x86_64.iso`.
- Before 1.0: each completed phase bumps the minor version; fixes and documentation bump the patch.
- From 1.0: major when users must migrate (for example, a different subvolume layout), minor when features are added, patch for fixes or rebuilds.
- Each `[archtiva]` package has its own `pkgver` in its PKGBUILD.

## 4. What we build and what we integrate

| In-house (small) | Integrated, no own code |
|---|---|
| archiso profile and build scripts | Arch Linux (core, extra, multilib), pacman |
| Calamares configuration and branding | Calamares, KDE Plasma, Discover, Flatpak/Flathub |
| `archtiva-settings` (defaults) | Btrfs, Snapper, snap-pac, grub-btrfs, zram-generator |
| `archtiva-branding` (logo, wallpapers, Plymouth, global theme) | Mesa, NVIDIA open, Vulkan, firmware, fwupd |
| `archtiva-keyring` and the `[archtiva]` repository | Steam, Proton, Lutris, Heroic, Bottles, gamemode, MangoHud |
| Archtiva Center (welcome, drivers, updates, extras) | reflector, pacman-contrib, CUPS, ufw + plasma-firewall |
| GitHub Actions workflows and tests | arch-update (if the evaluation confirms it) |

## 5. Main risks

| Risk | Impact | Mitigation |
|---|---|---|
| Arch breakage (e.g. the NVIDIA 590 change) | High | Weekly CI builds, blocking news, snapshots, LTS kernel |
| Single maintainer | High | Little in-house code, everything documented and automated |
| Calamares or KDE changes | Medium | Configuration only, versions tracked in CI |
| Secure Boot required on some machines | Medium | Clear documentation; `sbctl` later |
| ISO over 2 GiB | Medium | Package selection and an external mirror |
| Name and logo versus the Arch trademark | Medium | Ask Arch and use a distinct logo before publishing |
| AUR security | Medium | Kept out of the store, optional with a warning |
| Repository signing keys | High | Offline primary key; signing subkey in Actions secrets |
| VirtualBox tests not representative (3D, Wayland) | Medium | Live-USB tests on real hardware before every release |

## 6. Hardware requirements

**Current host:** Intel i5-14400F (10 cores, 16 threads), 16 GB RAM, NVIDIA RTX 4060, 108 GB free on C:. Hyper-V is active, so VirtualBox runs on top of it: slower, and no nested virtualisation.

| Machine | CPU | RAM | Disk | Notes |
|---|---|---|---|---|
| Build VM (Arch Linux) | 4–6 vCPU | 8 GB | 80 GB dynamic | EFI. Builds packages and the ISO. The current "Archtiva" VM has 2 vCPU, 4 GB and 10 GB, so it needs to be enlarged |
| ISO test VM | 2–4 vCPU | 4 GB | 40 GB dynamic | EFI, VMSVGA with 128 MB video memory. Recreated for every test |
| Real hardware | — | — | USB stick of 8 GB or more | The host's RTX 4060 can be used to test NVIDIA from the live USB |
| GitHub Actions | standard runner | 16 GB | ~14 GB free | Enough for an ISO under 2 GiB |

**Archtiva minimum requirements (target):** x86-64 with UEFI, 4 GB RAM (8 GB recommended), 40 GB disk (64 GB recommended because of snapshots), and a Vulkan-capable GPU for gaming.
