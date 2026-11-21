# Signing the `[arctiva]` repository

> Versión en castellano: [../es/firma.md](../es/firma.md)

The Arctiva package repository (D-01) is signed with GPG. This document explains how the keys are organised and prepared; it is the part a person does by hand, once.

## How it works

- **Primary key** (ed25519, certification only, expires after 5 years): **kept offline**. It lives on a USB stick and, optionally, on paper; never on a development machine or on GitHub.
- **Signing subkey** (ed25519, expires after 2 years): lives in GitHub Actions secrets. Signing packages and the repository database is always done by CI, never by a development machine.
- The **`arctiva-keyring` package** ships the public key and marks it as trusted on the installed system (`pacman-key --populate arctiva`).
- Packages are published as the files of a fixed release (`x86_64`) of the public repository `catlinux/arctiva-repo`.

## Setup (once)

Done on the Debian machine, running the commands below in a temporary directory that is deleted afterwards.

1. On GitHub, create the **public** repository `catlinux/arctiva-repo` with a README and an empty release `x86_64` (title "Arctiva repository (x86_64)").
2. Generate the keys:

```
export GNUPGHOME="$(mktemp -d)"; chmod 700 "$GNUPGHOME"
gpg --quick-gen-key "Arctiva Repository <10865946+catlinux@users.noreply.github.com>" ed25519 cert 5y
FPR=$(gpg --with-colons --list-keys | awk -F: '/^fpr/{print $10; exit}')
gpg --quick-add-key "$FPR" ed25519 sign 2y
SUB=$(gpg --with-colons --list-keys "$FPR" | awk -F: '/^sub/{s=1; next} s && /^fpr/{print $10; s=0}' | tail -1)
gpg --armor --export "$FPR" > arctiva.gpg                    # public: goes into the repository
gpg --armor --export-secret-subkeys "${SUB}!" > subkey.asc   # GitHub secret; delete afterwards
gpg --armor --export-secret-keys "$FPR" > primary-OFFLINE.asc
cp "$GNUPGHOME"/openpgp-revocs.d/*.rev revocation-OFFLINE.rev
echo "$FPR"
```

3. Keep `primary-OFFLINE.asc` and `revocation-OFFLINE.rev` on a USB stick stored separately (and `paperkey` on paper if wished). Then `shred -u subkey.asc` (once loaded into GitHub) and `rm -rf "$GNUPGHOME"`.
4. In `catlinux/arctiva` → Settings → Secrets and variables → Actions, create three secrets:
   - `ARCTIVA_SIGNING_KEY`: the contents of `subkey.asc`.
   - `ARCTIVA_SIGNING_PASSPHRASE`: the key's passphrase.
   - `ARCTIVA_REPO_TOKEN`: a fine-grained token with **Contents: Read and write** on `arctiva-repo` only, expiring in 1 year.
5. Hand the project the **public fingerprint** (40 characters) and `arctiva.gpg` (the public key). Nothing else: the private key is never shared.

## Renewing the subkey

Before it expires (2 years), with the primary key from the USB stick in a temporary directory: `gpg --quick-add-key <FINGERPRINT> ed25519 sign 2y`, export the new subkey with `--export-secret-subkeys`, replace `ARCTIVA_SIGNING_KEY` and publish `arctiva.gpg` again through `arctiva-keyring`. Renew the token too before its year is up.

## If a key is compromised

Publish the revocation certificate (`revocation-OFFLINE.rev`), add the fingerprint to `arctiva-revoked` in `arctiva-keyring` and generate a new set of keys.
