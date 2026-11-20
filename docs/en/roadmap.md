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
| 5. Applications and Windows | 0.6.0 | Store and compatibility | Store according to the D-07 study, with repositories, Flathub and AUR kept apart; Bottles and the `.exe` dialog; Steam, Proton and Heroic working on real hardware with NVIDIA and AMD or Intel |
| 6. Identity | 0.7.0 | A consistent visual identity | Approved vector logo; Plymouth boot splash, login, global theme, wallpapers and Calamares branding |
| 7. Beta | 0.8.0–0.9.x | Quality and release | Real-hardware test matrix; user documentation; signed release pipeline with a mirror; public beta |
| Stable | 1.0.0 | First stable release | No open blocking bugs; monthly release process documented |

## Working principles

- A phase does not start until the previous one meets its definition of done.
- Every behaviour change ships with its version bump, CHANGELOG entry and updated documentation in the same commit.
- ISO builds and tests run in virtual machines or GitHub Actions, never on the main computer.
