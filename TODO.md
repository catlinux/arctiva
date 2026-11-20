# TODO

> Versión en castellano: [TODO.es.md](TODO.es.md)

Pending work grouped by priority. Phases and decisions: [roadmap](docs/en/roadmap.md) · [architecture](docs/en/architecture.md).

## High — phase 0 (foundations)

- [ ] Review and approve the remaining architecture decisions (D-14 already approved).
- [ ] Approve the new logo in `branding/logo/` (D-13).
- [ ] Rename the GitHub repository to `arctiva` and update the local remote.
- [ ] Enlarge the build VM (4–6 vCPU, 8 GB RAM, 80 GB disk) and install Arch Linux with `archiso`.
- [ ] Build the stock `releng` ISO in the VM and document the verified steps in the development guide.
- [ ] Decide when the repository becomes public.

## Medium — phase 1 (minimal live ISO)

- [ ] Arctiva archiso profile derived from `releng`, with Plasma and automatic live login.
- [ ] Reproducible build script with a pinned Arch Linux Archive date.
- [ ] GitHub Actions workflow: ISO build and QEMU boot test.
- [ ] Measure the ISO size and confirm it stays under 2 GiB (D-14).

## Medium — studies

- [ ] Store and sources study (D-07): compare Discover with a custom back-end, Pamac, Bauh, Octopi and an in-house store; proof of concept and final decision.
- [ ] Installer interface design (D-03): mock-ups of the QML pages and the partitioning stylesheet, before phase 2.

## Later

- Phases 2 to 7 as described in the roadmap.

## Rejected

- **Forking or holding back official Arch packages:** it breaks compatibility with the AUR and multiplies maintenance (D-01).
- **Discover's PackageKit back-end:** poor support on Arch and risk of partial upgrades (D-07).
- **An installer written from scratch:** partitioning and resizing Windows is where data loss happens; Calamares is customised instead (D-03).
- **Legacy BIOS in 1.0:** doubles the test matrix for very little benefit (D-04).
- **Splitting the ISO into parts:** USB writing tools need a single file (D-14).
- **Native Bottles package:** upstream only supports Flatpak (D-12).
