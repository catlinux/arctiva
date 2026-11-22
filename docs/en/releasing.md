# Releasing Arctiva

> Versión en castellano: [../es/publicacion.md](../es/publicacion.md)

The ISO is published by the `.github/workflows/release.yml` workflow, triggered by pushing a `vX.Y.Z` tag. Tags are created by the maintainer.

## Before tagging

1. `VERSION` and the `## [X.Y.Z]` section of `CHANGELOG.md` (and `CHANGELOG.es.md`) must match the tag: the workflow checks it and fails otherwise.
2. The "ISO" CI workflow is green for the same commit (with the date in `iso/archive-date`; if the Arch Archive was down, that build used the current mirrors and does **not** count: repeat it when the Archive answers).
3. The ISO has been tested on real hardware (see `docs/en/testing.md` when it exists).
4. For a test version (0.x) the workflow marks the release as a *prerelease*.

## What the workflow does

1. Checks the tag, `VERSION` and the changelog.
2. Builds the ISO with the pinned Archive date from `iso/archive-date`. **There is no fallback:** if the Archive is down it fails (a published ISO must be rebuildable identically).
3. Boot test in QEMU (UEFI).
4. Signs the ISO with the repository's signing subkey (`ARCTIVA_SIGNING_KEY` and `ARCTIVA_SIGNING_PASSPHRASE` secrets, see [signing.md](signing.md)): detached `.sig`, without leaving the key on disk.
5. Verifies the checksum and signature with the repository's public key.
6. Creates the release with the ISO, `.sha256`, `.sig` and notes (that version's CHANGELOG section).

## Verifying a download

```
sha256sum -c arctiva-X.Y.Z-x86_64.iso.sha256
gpg --import arctiva.gpg                        # public key: packages/arctiva-keyring/arctiva.gpg
gpg --verify arctiva-X.Y.Z-x86_64.iso.sig arctiva-X.Y.Z-x86_64.iso
```

The key fingerprint is in [signing.md](signing.md); compare it before trusting the signature.

## After publishing

- Update the Discussions Q&A that mention the version or say "there is no ISO" (`.agents/plans/discussions/qa-discussions.md`) and tell the website.
- Test the published ISO: download, verify and boot it in a virtual machine.
