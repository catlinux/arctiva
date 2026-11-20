# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Versión en castellano: [CHANGELOG.es.md](CHANGELOG.es.md)

## [Unreleased]

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
