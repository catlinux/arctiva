# Arctiva roadmap

> Versión en castellano: [../es/hoja-de-ruta.md](../es/hoja-de-ruta.md)

Each phase has a verifiable goal and ends with a release. The decisions referenced (D-xx) are in [architecture.md](architecture.md). Pending tasks are detailed in [TODO.md](../../TODO.md).

| Phase | Version | Goal | Definition of done |
|---|---|---|---|
| 0. Foundations | 0.1.x | Documentation, approved decisions, licence, trademark and build environment | Architecture approved; licence applied; the build VM produces the stock `releng` ISO unchanged |
| 1. Minimal live ISO | 0.2.0 | Own archiso profile with Plasma in live mode | The ISO boots in VirtualBox (UEFI) to the desktop with automatic login; it rebuilds from a pinned Arch Linux Archive date; CI builds it and passes the QEMU boot test; its size is measured (D-14) |
| 2. Installer | 0.3.0 | Tailored Calamares with offline installation (D-03) | Own QML interface approved; full installation without a terminal in a VM: language, keyboard, time zone, user, automatic and manual partitioning, Btrfs + Snapper + GRUB with bootable snapshots, `linux` and `linux-lts`; installing alongside Windows tested |
| 3. Own repository and hardware | 0.4.0 | Signed `[arctiva]` and GPU detection | Repository published and signed with `arctiva-keyring`; `arctiva-settings` and provisional `arctiva-branding`; GPU detection in the installer; "Gaming" profile with multilib |
| 4. Arctiva Center | 0.5.0 | Welcome, drivers, updates and extras | Complete update flow (D-08) tested with a news item that requires manual intervention; extras catalogue; arch-update evaluation documented |
| 5. Applications and Windows | 0.6.0 | Store and compatibility | In-house store in Arctiva Center (D-07), with repositories, Flathub and AUR kept apart; Bottles and the `.exe` dialog; Steam, Proton and Heroic working on real hardware with NVIDIA and AMD or Intel |
| 6. Identity | 0.7.0 | A consistent visual identity | Approved vector logo; graphical GRUB theme, Plymouth boot splash, login, global theme, wallpapers and Calamares branding |
| 7. Beta | 0.8.0–0.9.x | Quality and release | Real-hardware test matrix; user documentation; signed release pipeline with a mirror; public beta |
| Stable | 1.0.0 | First stable release | No open blocking bugs; monthly release process documented |

## Detailed plan

Status of each work item: `[x]` done (with the version that closed it) and `[ ]` pending. The most immediate pending work, by priority, is in [TODO.md](../../TODO.md).

### Phase 0: foundations (0.1.x) — done

- [x] Feasibility analysis, architecture (D-01…D-16) and initial bilingual documentation (0.1.0)
- [x] GPL-3.0-or-later licence and trademark policy in `TRADEMARKS` (0.1.2)
- [x] The Arctiva name and a vector logo in colour, monochrome and icon versions (0.1.1–0.1.3)
- [x] Build VM with Arch and `archiso`; the official `releng` ISO builds and boots (0.1.4)
- [x] All architecture decisions approved (0.1.5–0.1.6)
- [x] Make the repository public (0.3.11)

### Preliminary studies

- [x] E1: store and application sources; in-house store in Arctiva Center (D-07) (0.1.6)
- [x] E2: installer design, encryption and Windows warnings (D-03, D-04) (0.1.7)
- [ ] Store proof of concept in the VM (before phase 5)
- [ ] Installer checks in the VM (before phase 2): Calamares QML modules, reading the launcher's result, encryption with a single passphrase, snapshot with an encrypted root, `os-prober`, reach of `stylesheet.qss`

### Phase 1: minimal live ISO (0.2.0) — done

- [x] `iso/` archiso profile derived from `releng`, UEFI-only boot (0.2.0)
- [x] Plasma with automatic login for the `live` user and a "safe graphics" entry (0.2.0)
- [x] Reproducible `build.sh` with an Arch Linux Archive date (0.2.0)
- [x] Size measured: 1.75 GiB, under the 1.9 GiB limit (D-14) (0.2.0)
- [x] CI workflow with build and QEMU boot test (0.2.0)
- [x] Docker build on any Linux (0.2.0)
- [x] `tests/run-live.sh`: boot and view the ISO in the browser from another computer (0.2.0)

### Phase 2: installer (0.3.0)

- [x] `calamares` 3.4.3 and `ckbcomp` packages, and a local repository for the ISO (0.2.1)
- [x] Base configuration: automatic and manual partitioning, Btrfs with subvolumes, optional LUKS1 with a single passphrase, GRUB, Snapper with bootable snapshots (0.2.2)
- [x] Kernel copied to the installed system, live-only bits removed and `linux-lts` when online (0.2.2)
- [x] Launcher and "Check" page (BitLocker, Windows Fast Startup) (0.2.3)
- [x] QML interface with the Arctiva identity and approved mock-ups (0.2.4–0.2.6)
- [x] Basic, Gaming and Office profiles (0.2.7–0.2.8)
- [x] Tests in virtual machines: installation without a terminal, alongside Windows, encrypted, manual partitioning

### Phase 3: own repository and hardware (0.4.0)

- [x] Signing key (offline master, subkey in CI) and the `arctiva-keyring` package (0.3.6)
- [x] Signed and published `[arctiva]` repository, with package builds in CI (0.3.9)
- [x] `arctiva-settings` (defaults, zram, multilib, reflector) and provisional `arctiva-branding`
- [x] GPU detection (D-10) in the installer (0.3.2), shared with Arctiva Center (0.3.14)
- [x] Complete "Gaming" profile with multilib (D-11) (0.3.2: `lib32-nvidia-utils` with Steam)

### Phase 4: Arctiva Center (0.5.0)

- [x] Base PySide6 application and polkit helper with a closed set of operations (0.3.11)
- [ ] First-boot welcome
- [x] Drivers (0.3.14)
- [x] Updates (D-08): blocking news, sensitive packages, `.pacnew`, translated errors (0.3.12)
- [x] arch-update evaluation documented
- [x] Extras catalogue (0.3.15)
- [ ] GRUB reinstalled on the EFI partition when the `grub` package is upgraded

### Phase 5: applications and Windows (0.6.0)

- [ ] "Applications" store with repositories, Flathub and AUR kept apart (D-07)
- [ ] Bottles and a dialog to open `.exe` and `.msi` files (D-12)
- [ ] Steam, Proton and Heroic tested on real hardware with NVIDIA and with AMD or Intel
- [ ] Remove Discover from the live ISO

### Phase 6: identity (0.7.0)

- [x] Approved vector logo (0.1.6)
- [ ] Corporate typeface and the logo tagline as paths
- [ ] Graphical GRUB theme (menu, snapshots submenu, live ISO), Plymouth, login screen, global theme and wallpapers
- [ ] Calamares and Arctiva Center branding

### Phase 7: beta (0.8.0–0.9.x)

- [ ] Real-hardware test matrix, once everything is implemented: USB stick on the PC (NVIDIA RTX 4060) and a laptop with Windows and Manjaro (replace Manjaro with Arctiva, keeping Windows and its EFI partition)
- [ ] User documentation
- [ ] Signed release (ISO, `sha256`, GPG signature) with an external mirror
- [ ] Public beta and own help channels

### Stable (1.0.0)

- [ ] No open blocking bugs
- [ ] Monthly release process documented
- [ ] Review of the "Arctiva" trademark before release

## Working principles

- A phase does not start until the previous one meets its definition of done.
- Every behaviour change ships with its version bump, CHANGELOG entry and updated documentation in the same commit.
- ISO builds and tests run in virtual machines or GitHub Actions, never on the main computer.
