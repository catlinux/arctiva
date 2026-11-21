# Firma del repositorio `[arctiva]`

> English version: [../en/signing.md](../en/signing.md)

El repositorio de paquetes de Arctiva (D-01) está firmado con GPG. Este documento explica cómo se organizan las claves y cómo se preparan; es la parte que hace una persona a mano, una sola vez.

## Cómo funciona

- **Clave primaria** (ed25519, solo certifica, caduca a los 5 años): **fuera de línea**. Se guarda en un USB y, si se quiere, en papel; nunca en un equipo de desarrollo ni en GitHub.
- **Subclave de firma** (ed25519, caduca a los 2 años): vive en los secretos de GitHub Actions. La firma de paquetes y de la base del repositorio la hace siempre el CI, nunca un equipo de desarrollo.
- El **paquete `arctiva-keyring`** lleva la clave pública y la marca como de confianza en el sistema instalado (`pacman-key --populate arctiva`).
- Los paquetes se publican como archivos de una release fija (`x86_64`) del repositorio público `catlinux/arctiva-repo`.

## Preparación (una vez)

Se hace en el Debian, con las órdenes de abajo en un directorio temporal que se borra al terminar.

1. Crear en GitHub el repositorio **público** `catlinux/arctiva-repo`, con un README y una release `x86_64` vacía (título «Arctiva repository (x86_64)»).
2. Generar las claves:

```
export GNUPGHOME="$(mktemp -d)"; chmod 700 "$GNUPGHOME"
gpg --quick-gen-key "Arctiva Repository <10865946+catlinux@users.noreply.github.com>" ed25519 cert 5y
FPR=$(gpg --with-colons --list-keys | awk -F: '/^fpr/{print $10; exit}')
gpg --quick-add-key "$FPR" ed25519 sign 2y
SUB=$(gpg --with-colons --list-keys "$FPR" | awk -F: '/^sub/{s=1; next} s && /^fpr/{print $10; s=0}' | tail -1)
gpg --armor --export "$FPR" > arctiva.gpg                    # pública: va al repositorio
gpg --armor --export-secret-subkeys "${SUB}!" > subclave.asc # secreto de GitHub; borrar después
gpg --armor --export-secret-keys "$FPR" > primaria-OFFLINE.asc
cp "$GNUPGHOME"/openpgp-revocs.d/*.rev revocacion-OFFLINE.rev
echo "$FPR"
```

3. Guardar `primaria-OFFLINE.asc` y `revocacion-OFFLINE.rev` en un USB que se conserve aparte (y `paperkey` en papel si se quiere). Después, `shred -u subclave.asc` (una vez cargada en GitHub) y `rm -rf "$GNUPGHOME"`.
4. En `catlinux/arctiva` → Settings → Secrets and variables → Actions, crear tres secretos:
   - `ARCTIVA_SIGNING_KEY`: contenido de `subclave.asc`.
   - `ARCTIVA_SIGNING_PASSPHRASE`: la contraseña de la clave.
   - `ARCTIVA_REPO_TOKEN`: token *fine-grained* con permiso **Contents: Read and write** solo sobre `arctiva-repo` y caducidad de 1 año.
5. Entregar al proyecto la **huella pública** (40 caracteres) y `arctiva.gpg` (la clave pública). Nada más: la clave privada no se comparte.

## Renovar la subclave

Antes de que caduque (2 años), con la primaria desde el USB en un directorio temporal: `gpg --quick-add-key <HUELLA> ed25519 sign 2y`, exportar la nueva subclave con `--export-secret-subkeys`, sustituir `ARCTIVA_SIGNING_KEY` y publicar de nuevo `arctiva.gpg` con `arctiva-keyring`. Renovar también el token antes de que cumpla su año.

## Si se compromete una clave

Se publica el certificado de revocación (`revocacion-OFFLINE.rev`), se añade la huella a `arctiva-revoked` de `arctiva-keyring` y se genera un juego nuevo de claves.
