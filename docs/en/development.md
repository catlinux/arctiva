# Development guide

> Versión en castellano: [../es/desarrollo.md](../es/desarrollo.md)

## Environment

- **Workstation:** Windows 11 with Visual Studio Code and Git. Editing and repository management happen here; nothing is built here.
- **Build VM:** Arch Linux in VirtualBox (EFI, 4–6 vCPU, 8 GB RAM, 80 GB dynamic disk). Builds packages and the ISO with `archiso`.
- **Test VM:** recreated for every ISO (EFI, 2–4 vCPU, 4 GB, 40 GB, VMSVGA with 128 MB).
- **CI:** GitHub Actions builds and tests from a clean state (see D-15 in [architecture.md](architecture.md)).

Detailed VM setup steps will be documented when phase 0 is complete, once they have been verified.

> Hyper-V is active on the host, so VirtualBox runs on top of it: slower, and no nested virtualisation. QEMU/KVM tests run in CI, or inside the build VM if performance allows.

## Line endings

The repository enforces LF line endings (`.gitattributes`). Shell scripts and PKGBUILDs with CRLF fail on Linux.

## Versioning

- SemVer `x.y.z` in the [`VERSION`](../../VERSION) file; policy in D-16.
- Every behaviour change bumps the version and adds an entry to both changelogs (`CHANGELOG.md` in English and `CHANGELOG.es.md` in Spanish) in the same commit.
- Unversioned changes go under `## [Unreleased]` / `## [Sin publicar]`.
- `vX.Y.Z` tags are created only when an approved version is released.

## Documentation

- Bilingual: the English root files (`README.md`, `CHANGELOG.md`, `TODO.md`) have a Spanish counterpart (`*.es.md`); `docs/en/` and `docs/es/` contain the same documents.
- Both languages are updated together in the same commit. A document without its counterpart is a bug.
- Architecture decisions are recorded in [architecture.md](architecture.md) with their rationale.

## Commits

- Descriptive messages in Spanish, one topic per commit.
- Secrets (signing keys, tokens) are never committed: they live in GitHub Actions secrets or outside the repository.
