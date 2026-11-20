# TODO

> Versión en castellano: [TODO.es.md](TODO.es.md)

Pending work grouped by priority. Phases and decisions: [roadmap](docs/en/roadmap.md) · [architecture](docs/en/architecture.md).

## High — phase 0 (foundations)

- [ ] Decide when the repository becomes public.

## Medium — phase 1 (minimal live ISO)

- [ ] Arctiva archiso profile derived from `releng`, with Plasma and automatic live login.
- [ ] Reproducible build script with a pinned Arch Linux Archive date.
- [ ] GitHub Actions workflow: ISO build and QEMU boot test.
- [ ] Measure the ISO size and confirm it stays under 2 GiB (D-14).

## Medium — studies

- [ ] Store proof of concept (D-07) in the VM: AppStream catalogue, `pyalpm` on a temporary database, installation with `pacman -Syu --needed` through a polkit helper, Flatpak with progress and `flatpak-kcm`, and the AUR flow with PKGBUILD, diff and `paru`. Before phase 5.
- [ ] Installer interface design (D-03): mock-ups of the QML pages and the partitioning stylesheet, before phase 2.

## Later

- Phases 2 to 7 as described in the roadmap.
- Convert the tagline in `branding/logo/arctiva-logo.svg`, currently live text, to paths once the corporate typeface is chosen (D-13).
- Hibernation: an `@swap` subvolume with a swap file alongside zram (D-04). Out of scope for 1.0, which only has suspend.

## Rejected

- **Forking or holding back official Arch packages:** it breaks compatibility with the AUR and multiplies maintenance (D-01).
- **Discover's PackageKit back-end:** poor support on Arch and risk of partial upgrades (D-07).
- **Discover with a custom back-end, Pamac, Bauh or Octopi as the store:** Discover has no pacman back-end and no stable interface to write one; the others depend on the AUR, are stalled or lack Flatpak (D-07).
- **An installer written from scratch:** partitioning and resizing Windows is where data loss happens; Calamares is customised instead (D-03).
- **Legacy BIOS in 1.0:** doubles the test matrix for very little benefit (D-04).
- **Splitting the ISO into parts:** USB writing tools need a single file (D-14).
- **Native Bottles package:** upstream only supports Flatpak (D-12).
