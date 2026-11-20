#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Compila los PKGBUILD de packages/ y crea el repositorio local «arctiva-local» (pacman).
# Debe ejecutarse como root en Arch (o en un contenedor archlinux); makepkg corre como un
# usuario sin privilegios y puede instalar las dependencias de compilación con sudo.
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
dest="${1:?uso: $0 <directorio-del-repositorio>}"

[[ $EUID -eq 0 ]] || { echo "build-packages.sh: hay que ejecutarlo como root." >&2; exit 1; }
pacman -S --noconfirm --needed base-devel git sudo >/dev/null

id -u arctivabuild >/dev/null 2>&1 || useradd -m arctivabuild
echo 'arctivabuild ALL=(ALL) NOPASSWD: ALL' >/etc/sudoers.d/arctivabuild

mkdir -p -- "$dest"
build_dir="$(mktemp -d)"
trap 'rm -rf -- "$build_dir"' EXIT
cp -a -- "${repo_dir}/packages/." "$build_dir/"
# La configuración del instalador vive en installer/ y toma de ../ la versión (VERSION) y el logo
# (branding/logo/).
cp -a -- "${repo_dir}/installer" "${build_dir}/arctiva-calamares-config"
cp -- "${repo_dir}/VERSION" "${build_dir}/VERSION"
mkdir -p -- "${build_dir}/branding"
cp -a -- "${repo_dir}/branding/logo" "${build_dir}/branding/logo"
chown -R arctivabuild: "$build_dir" "$dest"

# Orden de dependencias: calamares necesita ckbcomp, y la configuración, calamares.
for name in ckbcomp calamares arctiva-calamares-config; do
    d="${build_dir}/${name}"
    echo "== Compilando $(basename -- "$d")"
    # makepkg no importa keys/pgp/ por sí solo: se hace aquí para verificar las firmas de las fuentes.
    for key in "$d"/keys/pgp/*.asc; do
        [[ -e "$key" ]] && sudo -u arctivabuild gpg --batch --quiet --import "$key"
    done
    sudo -u arctivabuild env PKGDEST="$dest" bash -c \
        'cd "$1" && makepkg --syncdeps --noconfirm --needed --noprogressbar' _ "$d"
    # Los paquetes dependientes (calamares → ckbcomp) necesitan los anteriores instalados.
    pacman -U --noconfirm --needed "$dest"/"$(basename -- "$d")"-[0-9]*.pkg.tar.zst >/dev/null
done

rm -f -- "$dest"/arctiva-local.db* "$dest"/arctiva-local.files*
repo-add "$dest/arctiva-local.db.tar.zst" "$dest"/*.pkg.tar.zst
