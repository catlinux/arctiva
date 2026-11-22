# TODO

> Versión en castellano: [TODO.es.md](TODO.es.md)

Pending work grouped by priority. Phases and decisions: [roadmap](docs/en/roadmap.md) · [architecture](docs/en/architecture.md).

## High — Arctiva Center

- [ ] AUR: opening a package on a system without `git` fails with "[Errno 2] No such file or directory: 'git'" (seen with `faugus-launcher`). The PKGBUILD review clones with `git` (`aur_backend.py`, `prepare`) before `aur-prepare` installs `git` and `base-devel`, which only runs on "Install" (`install`). Run `aur-prepare` before cloning, or check for `git` and offer to install it.

## Medium — phase 2 (installer)

- [ ] Live ISO with GRUB instead of systemd-boot (`bootmodes=('uefi.grub')`, `iso/grub/` with the Arctiva theme, remove `iso/efiboot/`): it needs an Arch machine to test `mkarchiso`; `tests/boot-test.sh` does not change (it boots the kernel directly).

- [ ] Booting a snapshot fails `systemd-remount-fs` (fstab asks for `subvol=/@` and the root is a grub-btrfs overlay). It still boots; consider hiding it.
- [ ] The installer's QML pages carry their texts in Spanish, Catalan and English inside the QML itself; move them to branding translations (`.ts`) so more languages can be added.
- [ ] Offline map on the "Language and region" page: Calamares' map downloads tiles from the Internet, so the page currently uses lists only.
- [ ] The profiles list needs Ctrl+click to pick several (Calamares uses extended selection; the hint is in the "Basic" text). A custom QML page would allow plain clicks.
- [ ] Re-test "Install alongside" with the new 25 GiB requirement (0.3.13) on a 60 GB disk with Windows.
- [ ] Lighter ISO: the base is already lean (installed 4.3 GiB, ISO 1.76 GiB of the 1.9 limit). Biggest items: `firefox` 307 MiB, `qt6-webengine` 284 MiB (needed by `purpose`→`kaccounts`, used by Spectacle and Gwenview), `llvm-libs` 165 MiB (Mesa), `linux-firmware-*` ~430 MiB (Intel 142, NVIDIA 104, Atheros 53, MediaTek 37, AMDGPU 28), `noto-fonts` 107 MiB. The only real lever is installing only the firmware that the detected hardware needs (phase 3).

## Medium — installer

- [ ] Ventoy in normal mode drops to an emergency shell (only "grub2 mode" boots): probably Ventoy recognises archiso by `/arch/` and Arctiva uses `install_dir="arctiva"`. Check in QEMU with a Ventoy disk; if confirmed, weigh switching `install_dir` to `arch` (it touches `unpackfs`, the installer and the scripts).
- [ ] Slow live boot from a USB stick: 1 min 53 s on a laptop through Ventoy (loader 32 s, kernel 49 s because archiso copies the 1.7 GiB system to RAM, userspace 25 s). Weigh `copytoram=n` (faster start, slower programs) or a progress message.
- [ ] On the installer's "Profiles" page, the profile image touches the right edge of the window.

## Medium — studies

- [ ] Installer checks in the VM, before phase 2 (D-03, D-04): what Calamares 3.4.3's `localeq`, `packagechooserq` and `notesqml` do and need; `os-prober` with Windows, BitLocker and Fast Startup; how far `stylesheet.qss` reaches on the disk page.

## Later

- Add `pv` to the live ISO so the copy to RAM at boot shows a progress bar (today mkinitcpio warns `pv not found` and falls back to `cp` with no feedback). Repeat the boot test.
- Arctiva Games (optional `arctiva-games` package and extra, 0.1.0, coded but **not tested on real hardware**): run a full Battle.net install in a VM with acceleration or real hardware and check the launcher stays open until Continue; diagnose the WoW private-server case with `lutris -d` (plan step 1); check Proton runner order per launcher on real hardware (Battle.net with the system `wine` crashes in its browser engine); implement `extract`, `move`, `merge`, `input_menu` and user-provided files; ask the Lutris team before publishing; manual test of popular lutris.net scripts (plan step 9). Details in the games plan.
- Installing from inside Windows (assistant that downloads the ISO, verifies it and writes the USB): parked by the maintainer, not planned.
- Phases 2 to 7 as described in the roadmap.
- Real-hardware tests (USB stick on the PC with the RTX 4060; laptop with Windows and Manjaro), only at the end, with everything implemented (phase 7). The "safe graphics" entry already works in VirtualBox.
- Hibernation: an `@swap` subvolume with a swap file alongside zram (D-04). Out of scope for 1.0, which only has suspend.
- Bit-for-bit reproducible ISO: two builds with the same Arch Linux Archive date have the same packages and size but different checksums (D-02).
- LUKS2 encryption with TPM2 or FIDO2 unlocking, once Calamares lets us choose the key derivation function (D-04).
- Encryption passphrase typed with the user's keyboard layout in GRUB (`grub-kbdcomp`) instead of the US one (D-04).

- Build the in-house packages (`packages/`) against the same Arch Linux Archive date as the ISO: it would mean downgrading the builder with `pacman -Syyuu`, which is only safe in a throwaway container, so for now the packages are built with the day's libraries (documented in `docs/en/development.md`). Revisit if Calamares ever fails to start because of a newer library than the ISO ships.

## Rejected

- **Forking or holding back official Arch packages:** it breaks compatibility with the AUR and multiplies maintenance (D-01).
- **Discover's PackageKit back-end:** poor support on Arch and risk of partial upgrades (D-07).
- **Discover with a custom back-end, Pamac, Bauh or Octopi as the store:** Discover has no pacman back-end and no stable interface to write one; the others depend on the AUR, are stalled or lack Flatpak (D-07).
- **An installer written from scratch:** partitioning and resizing Windows is where data loss happens; Calamares is customised instead (D-03).
- **LUKS2 with Argon2id or an unencrypted `/boot` in 1.0:** Argon2id has been reported to leave GRUB out of memory at boot, and a separate `/boot` breaks bootable snapshots (D-04).
- **Legacy BIOS in 1.0:** doubles the test matrix for very little benefit (D-04).
- **Splitting the ISO into parts:** USB writing tools need a single file (D-14).
- **Native Bottles package:** upstream only supports Flatpak (D-12).
- **Warning on the summary page when the root is not Btrfs:** Calamares does not put the partition table in GlobalStorage until the installation runs, so a QML page cannot know; the user guide explains that snapshots need a Btrfs root.
