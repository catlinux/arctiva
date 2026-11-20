# TODO

> Versión en castellano: [TODO.es.md](TODO.es.md)

Pending work grouped by priority. Phases and decisions: [roadmap](docs/en/roadmap.md) · [architecture](docs/en/architecture.md).

## High — phase 0 (foundations)

- [ ] Review and approve the architecture decisions D-01 to D-16.
- [ ] Choose and apply the project licence.
- [ ] Ask `trademarks@archlinux.org` whether the name "Archtiva" is acceptable (D-13).
- [ ] Redesign the logo so it does not resemble the Arch logo; vector (SVG) and monochrome versions (D-13).
- [ ] Enlarge the "Archtiva" build VM (4–6 vCPU, 8 GB RAM, 80 GB disk) and install Arch Linux with `archiso`.
- [ ] Build the stock `releng` ISO in the VM and document the verified steps in the development guide.
- [ ] Decide when the repository becomes public.

## Medium — phase 1 (minimal live ISO)

- [ ] Archtiva archiso profile derived from `releng`, with Plasma and automatic live login.
- [ ] Reproducible build script with a pinned Arch Linux Archive date.
- [ ] GitHub Actions workflow: ISO build and QEMU boot test.
- [ ] Measure the ISO size and confirm the GitHub Releases strategy (D-14).

## Later

- Phases 2 to 7 as described in the roadmap.

## Rejected

- **Forking or holding back official Arch packages:** it breaks compatibility with the AUR and multiplies maintenance (D-01).
- **Discover's PackageKit back-end:** poor support on Arch and risk of partial upgrades (D-07).
- **AUR inside the store:** unreviewed code exposed to non-technical users (D-07).
- **Pamac:** designed around Manjaro's repositories; it has broken with major pacman updates.
- **Legacy BIOS in 1.0:** doubles the test matrix for very little benefit (D-04).
- **Splitting the ISO into parts:** USB writing tools need a single file (D-14).
- **Native Bottles package:** upstream only supports Flatpak (D-12).
