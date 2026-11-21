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
      Espejos extra del Archive (misma estructura repos/AAAA/MM/DD/), por si
      archive.archlinux.org falla: variable ARCHIVE_MIRRORS, bases separadas por espacios.
  -o  Directorio de salida de la ISO (por defecto: ./out).
  -w  Directorio de trabajo de mkarchiso; no debe existir
      (por defecto: ${work_dir}). No uses /tmp: está en RAM.
  -l  Directorio con un repositorio pacman «arctiva-local» ya compilado
      (por defecto se compila uno desde packages/ en un directorio temporal).
  -c  Directorio que se conserva entre construcciones para el repositorio local:
      solo se recompila lo que ha cambiado de versión (y siempre la configuración
      del instalador). Ahorra compilar Calamares en cada ISO.
  -k  Conservar el directorio de trabajo (para medir qué ocupa espacio).
EOF
}

die() { echo "build.sh: $*" >&2; exit 1; }

keep_work=0
local_repo=""
cache_repo=""
while getopts 'd:o:w:l:c:kh' opt; do
    case "$opt" in
        k) keep_work=1 ;;
        c) cache_repo="$OPTARG" ;;
        l) local_repo="$OPTARG" ;;
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
    # Mismo día en todos los servidores: pacman pasa al siguiente si uno falla, sin mezclar épocas.
    bases=(https://archive.archlinux.org ${ARCHIVE_MIRRORS:-})
    servers=""
    for base in "${bases[@]}"; do
        servers+="Server = ${base%/}/repos/${archive_date}/\$repo/os/\$arch\\n"
    done
    # Falla pronto y con un mensaje útil si ningún servidor responde, en vez de a mitad de mkarchiso.
    ok=0
    for base in "${bases[@]}"; do
        for _ in 1 2 3; do
            if curl -fsI -m 20 -o /dev/null "${base%/}/repos/${archive_date}/core/os/x86_64/core.db"; then ok=1; break 2; fi
            sleep 10
        done
    done
    (( ok )) || die "ningún servidor del Arch Linux Archive responde. Reintenta más tarde, define ARCHIVE_MIRRORS o usa -d latest (ISO no reproducible)."
    sed -i "s|^Include = /etc/pacman.d/mirrorlist$|${servers%'\n'}|" "${stage}/profile/pacman.conf"
    SOURCE_DATE_EPOCH="$(date -u -d "${archive_date//\//-}" +%s)"
    export SOURCE_DATE_EPOCH
    echo "Paquetes: Arch Linux Archive del ${archive_date}."
fi

# Paquetes propios (packages/): repositorio local sin firma, solo hasta que exista el firmado (fase 3).
if [[ -n "$cache_repo" ]]; then
    local_repo="$cache_repo"
    "${repo_dir}/packages/build-packages.sh" "$local_repo"
elif [[ -z "$local_repo" ]]; then
    local_repo="$(mktemp -d /var/tmp/arctiva-repo.XXXXXX)"
    trap 'rm -rf -- "$stage" "$local_repo"' EXIT
    "${repo_dir}/packages/build-packages.sh" "$local_repo"
fi
[[ -f "${local_repo}/arctiva-local.db.tar.zst" ]] || die "${local_repo} no es un repositorio arctiva-local."
local_repo="$(cd -- "$local_repo" && pwd)"
printf '\n[arctiva-local]\nSigLevel = Optional TrustAll\nServer = file://%s\n' "$local_repo" \
    >>"${stage}/profile/pacman.conf"

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
