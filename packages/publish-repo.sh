#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Compila y firma los paquetes arctiva-* cuya versión no está en el repositorio publicado y sube
# el resultado a la release «x86_64» de catlinux/arctiva-repo. Solo se ejecuta en el CI, como root
# en un contenedor archlinux. Variables: ARCTIVA_SIGNING_KEY, ARCTIVA_SIGNING_PASSPHRASE y GH_TOKEN
# (token con escritura sobre arctiva-repo). La contraseña nunca va en una línea de órdenes.
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target=catlinux/arctiva-repo
server="https://github.com/${target}/releases/download/x86_64"
: "${ARCTIVA_SIGNING_KEY:?}" "${ARCTIVA_SIGNING_PASSPHRASE:?}" "${GH_TOKEN:?}"

pacman -Syu --noconfirm --needed base-devel git sudo github-cli gnupg curl >/dev/null
id -u arctivabuild >/dev/null 2>&1 || useradd -m arctivabuild
echo 'arctivabuild ALL=(ALL) NOPASSWD: ALL' >/etc/sudoers.d/arctivabuild

work="$(mktemp -d)"
# mktemp crea el directorio en 700: arctivabuild tiene que poder entrar en src/ y out/. La clave
# queda en gnupg/, que sigue siendo 700 y de root.
chmod 755 -- "$work"
export GNUPGHOME="$work/gnupg"
mkdir -m 700 -- "$GNUPGHOME"
trap 'gpgconf --kill gpg-agent || true; rm -rf -- "$work"' EXIT
out="$work/out"; mkdir -- "$out"; chown arctivabuild: "$out"

# Clave de firma: la subclave importada se deja lista en el agente (sin contraseña en la línea de órdenes).
echo 'allow-preset-passphrase' >"$GNUPGHOME/gpg-agent.conf"
printf '%s' "$ARCTIVA_SIGNING_KEY" | gpg --batch --quiet --import
read -r fpr grip < <(gpg --list-secret-keys --with-colons | awk -F: \
    '/^ssb/{s=($12 ~ /s/)} s&&/^fpr/{f=$10} s&&/^grp/{print f, $10; exit}')
[[ -n "${fpr:-}" && -n "${grip:-}" ]] || { echo "No hay subclave de firma en ARCTIVA_SIGNING_KEY." >&2; exit 1; }
gpgconf --launch gpg-agent
printf '%s' "$ARCTIVA_SIGNING_PASSPHRASE" | /usr/lib/gnupg/gpg-preset-passphrase --preset "$grip"

# Base publicada (no existe la primera vez): repo-add la amplía en lugar de empezar de cero.
# Con su firma: repo-add --verify comprueba la base publicada antes de ampliarla.
for f in arctiva.db arctiva.files; do
    curl -fsSL -o "$out/$f.tar.gz" "$server/$f" || { rm -f -- "$out/$f.tar.gz"; continue; }
    curl -fsSL -o "$out/$f.tar.gz.sig" "$server/$f.sig" || rm -f -- "$out/$f.tar.gz.sig"
done
published=""
[[ -e "$out/arctiva.db.tar.gz" ]] && published="$(tar -tzf "$out/arctiva.db.tar.gz" | grep '/$' || true)"

build_dir="$work/src"; mkdir -- "$build_dir"
cp -a -- "$repo_dir"/packages/arctiva-* "$build_dir/"
# El código de arctiva-center vive en center/ (su PKGBUILD lo busca en ../center).
cp -a -- "$repo_dir/center" "$build_dir/center"
# arctiva-branding toma el logo y los fondos de ../branding.
mkdir -- "$build_dir/branding"
cp -a -- "$repo_dir/branding/." "$build_dir/branding/"
chown -R arctivabuild: "$build_dir"

# Los arctiva-* que dependen de otros (arctiva-center) los toman de la base ya publicada, verificada
# con el anillo de este mismo repositorio (no con el publicado, que podría estar alterado).
if [[ -n "$published" ]]; then
    install -m644 -t /usr/share/pacman/keyrings -- "$repo_dir"/packages/arctiva-keyring/arctiva{.gpg,-trusted,-revoked}
    # La imagen archlinux no trae clave local con la que firmar las de confianza: --init la crea.
    pacman-key --init >/dev/null 2>&1
    pacman-key --populate arctiva >/dev/null
    printf '\n[arctiva]\nSigLevel = Required\nServer = %s\n' "$server" >>/etc/pacman.conf
    pacman -Sy >/dev/null
fi

# arctiva-center al final: depende de arctiva-branding y arctiva-hardware, que si cambian se compilan antes.
dirs=(); for d in "$build_dir"/arctiva-*; do [[ "$d" == */arctiva-center ]] || dirs+=("$d"); done
dirs+=("$build_dir/arctiva-center")

new=()
for d in "${dirs[@]}"; do
    name="$(basename -- "$d")"
    ver="$(sudo -u arctivabuild bash -c 'cd "$1" && source PKGBUILD && echo "${epoch:+$epoch:}$pkgver-$pkgrel"' _ "$d")"
    if grep -qx "${name}-${ver}/" <<<"$published"; then
        echo "== $name $ver ya publicado"; continue
    fi
    echo "== Compilando $name $ver"
    sudo -u arctivabuild env PKGDEST="$out" bash -c \
        'cd "$1" && makepkg --syncdeps --noconfirm --needed --noprogressbar' _ "$d"
    pacman -U --noconfirm --needed "$out"/"$name"-[0-9]*.pkg.tar.zst >/dev/null
    for p in "$out"/"$name"-"${ver#*:}"-*.pkg.tar.zst; do
        gpg --batch --yes --detach-sign --no-armor -u "${fpr}!" "$p"
        new+=("$p")
    done
done

if (( ${#new[@]} == 0 )); then echo "Nada que publicar."; exit 0; fi

cd -- "$out"
repo-add --sign --key "$fpr" --verify arctiva.db.tar.gz "${new[@]}"
# Los assets de GitHub no admiten enlaces: la base es un archivo real con su firma. repo-add deja
# arctiva.db y arctiva.db.sig como enlaces a los .tar.gz; se quitan antes de copiar.
for f in arctiva.db arctiva.files; do
    rm -f -- "$f" "$f.sig"
    cp -- "$f.tar.gz" "$f"; cp -- "$f.tar.gz.sig" "$f.sig"
done

# La release fija se crea la primera vez (el token tiene permiso de escritura sobre arctiva-repo).
gh release view x86_64 --repo "$target" >/dev/null 2>&1 ||
    gh release create x86_64 --repo "$target" --title 'Arctiva repository (x86_64)' \
        --notes 'Packages and database of the signed [arctiva] repository. Updated automatically.'

# Primero se sube todo y después se borran las versiones anteriores: mientras tanto, la base vieja
# sigue apuntando a archivos que existen.
gh release upload x86_64 --clobber --repo "$target" \
    arctiva.db arctiva.db.sig arctiva.files arctiva.files.sig "${new[@]}" "${new[@]/%/.sig}"
assets="$(gh release view x86_64 --repo "$target" --json assets --jq '.assets[].name')"
for p in "${new[@]}"; do
    base="$(basename -- "$p")"; pkg="${base%-*-*-*}"
    { grep -E "^${pkg}-[^-]+-[^-]+-[^-]+\.pkg\.tar\.zst(\.sig)?$" <<<"$assets" || true; } |
        { grep -v "^${base}" || true; } |
        while read -r old; do gh release delete-asset x86_64 "$old" --repo "$target" --yes; done
done
