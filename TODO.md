# TODO

> Versión en castellano: [TODO.es.md](TODO.es.md)

Pending work grouped by priority. Phases and decisions: [roadmap](docs/en/roadmap.md) · [architecture](docs/en/architecture.md).

## High — phase 0 (foundations)

- [ ] Decide when the repository becomes public.

## Medium — phase 1 follow-up

- [ ] Test the live ISO on real hardware from a USB stick (the PC's RTX 4060; laptop with Windows and Manjaro). The "safe graphics" entry already works in VirtualBox.

## Medium — studies

- [ ] Store proof of concept (D-07) in the VM: AppStream catalogue, `pyalpm` on a temporary database, installation with `pacman -Syu --needed` through a polkit helper, Flatpak with progress and `flatpak-kcm`, and the AUR flow with PKGBUILD, diff and `paru`. Before phase 5.
- [ ] Installer checks in the VM, before phase 2 (D-03, D-04): what Calamares 3.4.3's `localeq`, `packagechooserq` and `notesqml` do and need; that the "Check" page can read the launcher's result; encrypted install with a single passphrase prompt and GRUB unlock time; booting a snapshot with an encrypted root; `os-prober` with Windows, BitLocker and Fast Startup; how far `stylesheet.qss` reaches on the disk page.

## Later

- Phases 2 to 7 as described in the roadmap.
- Convert the tagline in `branding/logo/arctiva-logo.svg`, currently live text, to paths once the corporate typeface is chosen (D-13).
- Hibernation: an `@swap` subvolume with a swap file alongside zram (D-04). Out of scope for 1.0, which only has suspend.
- Bit-for-bit reproducible ISO: two builds with the same Arch Linux Archive date have the same packages and size but different checksums (D-02).
- LUKS2 encryption with TPM2 or FIDO2 unlocking, once Calamares lets us choose the key derivation function (D-04).
- Encryption passphrase typed with the user's keyboard layout in GRUB (`grub-kbdcomp`) instead of the US one (D-04).

## Rejected

- **Forking or holding back official Arch packages:** it breaks compatibility with the AUR and multiplies maintenance (D-01).
- **Discover's PackageKit back-end:** poor support on Arch and risk of partial upgrades (D-07).
- **Discover with a custom back-end, Pamac, Bauh or Octopi as the store:** Discover has no pacman back-end and no stable interface to write one; the others depend on the AUR, are stalled or lack Flatpak (D-07).
- **An installer written from scratch:** partitioning and resizing Windows is where data loss happens; Calamares is customised instead (D-03).
- **LUKS2 with Argon2id or an unencrypted `/boot` in 1.0:** Argon2id has been reported to leave GRUB out of memory at boot, and a separate `/boot` breaks bootable snapshots (D-04).
- **Legacy BIOS in 1.0:** doubles the test matrix for very little benefit (D-04).
- **Splitting the ISO into parts:** USB writing tools need a single file (D-14).
- **Native Bottles package:** upstream only supports Flatpak (D-12).
