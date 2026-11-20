#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Construye la ISO de Arctiva con mkarchiso a partir del perfil iso/ (D-02).
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
profile_src="${repo_dir}/iso"
out_dir="${PWD}/out"
work_dir="/var/tmp/arctiva-work"
archive_date="${ARCHIVE_DATE:-}"
# D-14: GitHub Releases admite menos de 2 GiB; el margen deja sitio a cambios pequeños.
max_size=$((19 * 1024 * 1024 * 1024 / 10))

usage() {
    cat <<EOF
Uso: sudo ./build.sh [-d AAAA/MM/DD|latest] [-o salida] [-w trabajo]

  -d  Fecha del Arch Linux Archive (por defecto, la de iso/archive-date).
      «latest» usa los mirrors del equipo, sin fecha fijada.
  -o  Directorio de salida de la ISO (por defecto: ./out).
  -w  Directorio de trabajo de mkarchiso; no debe existir
      (por defecto: ${work_dir}). No uses /tmp: está en RAM.
  -k  Conservar el directorio de trabajo (para medir qué ocupa espacio).
EOF
}

die() { echo "build.sh: $*" >&2; exit 1; }

keep_work=0
while getopts 'd:o:w:kh' opt; do
    case "$opt" in
        k) keep_work=1 ;;
        d) archive_date="$OPTARG" ;;
        o) out_dir="$OPTARG" ;;
        w) work_dir="$OPTARG" ;;
        h) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

[[ $EUID -eq 0 ]] || die "hay que ejecutarlo como root (sudo)."
command -v mkarchiso >/dev/null || die "falta mkarchiso (paquete archiso)."
[[ ! -e "$work_dir" ]] || die "el directorio de trabajo ${work_dir} ya existe; bórralo o usa -w."

[[ -n "$archive_date" ]] || archive_date="$(tr -d '[:space:]' <"${profile_src}/archive-date")"
version="$(tr -d '[:space:]' <"${repo_dir}/VERSION")"

stage="$(mktemp -d)"
trap 'rm -rf -- "$stage"' EXIT
cp -a -- "$profile_src" "${stage}/profile"

if [[ "$archive_date" == latest ]]; then
    echo "Paquetes: mirrors actuales del equipo (sin fecha fijada)."
else
    [[ "$archive_date" =~ ^[0-9]{4}/[0-9]{2}/[0-9]{2}$ ]] || die "fecha no válida: ${archive_date} (formato AAAA/MM/DD)."
    sed -i "s|^Include = /etc/pacman.d/mirrorlist$|Server = https://archive.archlinux.org/repos/${archive_date}/\$repo/os/\$arch|" \
        "${stage}/profile/pacman.conf"
    SOURCE_DATE_EPOCH="$(date -u -d "${archive_date//\//-}" +%s)"
    export SOURCE_DATE_EPOCH
    echo "Paquetes: Arch Linux Archive del ${archive_date}."
fi

export ARCTIVA_VERSION="$version"
mkdir -p -- "$out_dir"
mkarchiso_opts=(-v -w "$work_dir" -o "$out_dir")
(( keep_work )) || mkarchiso_opts+=(-r)
mkarchiso "${mkarchiso_opts[@]}" "${stage}/profile"

iso_name="arctiva-${version}-x86_64.iso"
iso="${out_dir}/${iso_name}"
[[ -f "$iso" ]] || die "no se ha generado ${iso}."
(cd -- "$out_dir" && sha256sum -- "$iso_name" >"${iso_name}.sha256")

size="$(stat -c %s -- "$iso")"
echo "ISO: ${iso}"
echo "Tamaño: ${size} bytes ($(numfmt --to=iec-i --suffix=B "$size"))"
if (( size > max_size )); then
    die "la ISO pasa de 1,9 GiB (límite de D-14)."
fi
