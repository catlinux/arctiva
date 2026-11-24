#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Prueba installer/scripts/install-bootloader con una raíz falsa y chroot, blkid, findmnt, mount,
# umount, dd y fsck.vfat falsos. No necesita root ni UEFI.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
script="${here}/../installer/scripts/install-bootloader"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "${tmp}/bin"

falso() { { echo '#!/usr/bin/env bash'; cat; } >"${tmp}/bin/$1"; chmod +x "${tmp}/bin/$1"; }

# grub-install falla las FAKE_FAIL primeras veces dejando una carpeta a medias.
falso chroot <<'FAKE'
shift
echo "chroot $*" >>"$FAKE_LOG"
[[ "$1" == grub-install ]] || exit 0
id=""
for a in "$@"; do [[ "$a" == --bootloader-id=* ]] && id="${a#*=}"; done
n=$(( $(cat "$FAKE_COUNT" 2>/dev/null || echo 0) + 1 )); echo "$n" >"$FAKE_COUNT"
mkdir -p "${FAKE_ESP}/EFI/${id}"
if (( n <= FAKE_FAIL )); then echo parcial >"${FAKE_ESP}/EFI/${id}/parcial"; exit 1; fi
echo "grub-nuevo (,gpt2)/@/boot/grub" >"${FAKE_ESP}/EFI/${id}/grubx64.efi"
FAKE
# Disco de la ESP: 1 ESP, 2 raíz destino, 3 otra Arctiva (Btrfs), 4 Windows, 5 LUKS ajeno, 6 LUKS propio.
falso lsblk <<'FAKE'
case "$*" in
    "-nrpo PKNAME -- /dev/esp") echo /dev/disco ;;
    "-nrpo NAME,PARTN -- /dev/disco") printf '%s\n' "/dev/esp 1" "/dev/root 2" "/dev/otra 3" "/dev/win 4" "/dev/luksotra 5" "/dev/lukspropia 6" ;;
    *) exit 1 ;;
esac
FAKE
falso mountpoint <<'FAKE'
exit 0
FAKE
falso findmnt <<'FAKE'
if [[ "$*" == *"${FAKE_ESP}"* ]]; then echo /dev/esp; else echo '/dev/root[/@]'; fi
FAKE
# Raíz destino 1111; otro sistema activo 2222 (sin cifrar) y LUKS 2222 y aaaa presentes.
falso blkid <<'FAKE'
case "$*" in
    "-s UUID -o value /dev/root") echo 11111111-1111-1111-1111-111111111111 ;;
    "-s TYPE -o value /dev/otra") echo btrfs ;;
    "-s TYPE -o value /dev/win") echo ntfs ;;
    "-s TYPE -o value /dev/luksotra"|"-s TYPE -o value /dev/lukspropia") echo crypto_LUKS ;;
    "-s UUID -o value /dev/luksotra") echo 22222222-2222-2222-2222-222222222222 ;;
    "-s UUID -o value /dev/lukspropia") echo aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa ;;
    "-t TYPE=crypto_LUKS -s UUID -o value") printf '%s\n' aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa 22222222-2222-2222-2222-222222222222 ;;
    "-U 11111111-1111-1111-1111-111111111111") echo /dev/root ;;
    "-U 22222222-2222-2222-2222-222222222222") echo /dev/other ;;
    *) exit 2 ;;
esac
FAKE
for c in umount mount; do
    falso "$c" <<'FAKE'
echo "$(basename "$0") $*" >>"$FAKE_LOG"
FAKE
done
falso dd <<'FAKE'
echo "dd $*" >>"$FAKE_LOG"
for a in "$@"; do if [[ "$a" == of=* ]]; then : >"${a#of=}"; fi; done
exit 0
FAKE
falso fsck.vfat <<'FAKE'
echo "fsck.vfat $*" >>"$FAKE_LOG"
[[ "$1" == -a ]] && exit "${FAKE_FSCK_A:-0}"
exit "${FAKE_FSCK_N:-0}"
FAKE
export PATH="${tmp}/bin:${PATH}"

r="${tmp}/raiz"
esp="${r}/boot/efi"
fallos=0

# preparar [contenido de EFI/arctiva/grubx64.efi] [contenido de EFI/Boot/BOOTX64.EFI]
preparar() {
    rm -rf -- "$r" "${tmp}/sys" "${tmp}/count"
    mkdir -p "${esp}/EFI" "${r}/etc" "${tmp}/sys/firmware/efi"
    echo 64 >"${tmp}/sys/firmware/efi/fw_platform_size"
    if [[ -n "${1:-}" ]]; then mkdir -p "${esp}/EFI/arctiva"; printf '%s\n' "$1" >"${esp}/EFI/arctiva/grubx64.efi"; fi
    if [[ -n "${2:-}" ]]; then mkdir -p "${esp}/EFI/Boot"; printf '%s\n' "$2" >"${esp}/EFI/Boot/BOOTX64.EFI"; fi
    : >"${tmp}/log"
    export FAKE_LOG="${tmp}/log" FAKE_COUNT="${tmp}/count" FAKE_ESP="$esp" FAKE_FAIL=0 FAKE_FSCK_A=0 FAKE_FSCK_N=0
    export ARCTIVA_INSTALL_BOOTLOADER_SYS="${tmp}/sys"
}
# probar <nombre> <código esperado> <id esperado o -> [condición extra]
probar() {
    local nombre="$1" esperado="$2" id="$3" extra="${4:-true}" codigo=0 bien=1
    bash "$script" "$r" >"${tmp}/out" 2>&1 || codigo=$?
    [[ "$codigo" == "$esperado" ]] || bien=0
    if [[ "$id" != - ]]; then
        [[ "$(cat "${r}/etc/arctiva/bootloader-id" 2>/dev/null)" == "$id" && -f "${esp}/EFI/${id}/grubx64.efi" ]] || bien=0
        grep -q "chroot grub-mkconfig" "${tmp}/log" || bien=0
    fi
    eval "$extra" || bien=0
    if (( bien )); then echo "ok    ${nombre}"; else
        echo "FALLO ${nombre} (código ${codigo}, esperado ${esperado})"; sed 's/^/      /' "${tmp}/out"; fallos=$((fallos + 1))
    fi
}
reserva() { cat "${esp}/EFI/Boot/BOOTX64.EFI" 2>/dev/null; }

preparar; probar "ESP vacía: arctiva y reserva creada" 0 arctiva '[[ "$(reserva)" == grub-nuevo* ]]'
preparar "search.fs_uuid 33333333-3333-3333-3333-333333333333"
probar "reinstalación (UUID que ya no existe): arctiva" 0 arctiva
preparar "search.fs_uuid 22222222-2222-2222-2222-222222222222"
probar "otra Arctiva activa: arctiva-2 sin tocarla" 0 arctiva-2 'grep -q 2222 "${esp}/EFI/arctiva/grubx64.efi"'
preparar "imagen sin marcas"; probar "imagen desconocida: arctiva-2" 0 arctiva-2
preparar "imagen sin marcas"; mkdir -p "${esp}/EFI/arctiva-2"; probar "carpeta vacía sin imagen: se salta" 0 arctiva-3 '[[ -d "${esp}/EFI/arctiva-2" ]]'
preparar "search.fs_uuid 44444444-4444-4444-4444-444444444444 cryptomount -u 22222222222222222222222222222222"
echo 'luks-aaaa UUID=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa none luks' >"${r}/etc/crypttab"
probar "otra Arctiva cifrada activa: arctiva-2" 0 arctiva-2
preparar "search.fs_uuid 44444444-4444-4444-4444-444444444444 cryptomount -u AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
printf '# comentario\nluks-aaaa UUID=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa none luks\n' >"${r}/etc/crypttab"
probar "LUKS de esta instalación: arctiva" 0 arctiva
preparar "(,gpt3)/@/boot/grub"; probar "mismo disco, otra Arctiva en gpt3: arctiva-2" 0 arctiva-2
preparar "(,gpt2)/@/boot/grub"; probar "mismo disco, gpt2 es la raíz nueva: arctiva" 0 arctiva
preparar "(,gpt4)/@/boot/grub"; probar "mismo disco, gpt4 ya no es Linux: arctiva" 0 arctiva
preparar "(,gpt9)/@/boot/grub"; probar "mismo disco, gpt9 ya no existe: arctiva" 0 arctiva
preparar "(,gpt5)/@/boot/grub"; probar "mismo disco, LUKS ajeno en gpt5: arctiva-2" 0 arctiva-2
preparar "(,gpt6)/@/boot/grub"
echo 'luks-aaaa UUID=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa none luks' >"${r}/etc/crypttab"
probar "mismo disco, LUKS propio en gpt6: arctiva" 0 arctiva
preparar "(cryptouuid/22222222222222222222222222222222)/@/boot/grub"
probar "prefijo cryptouuid de un LUKS ajeno: arctiva-2" 0 arctiva-2
preparar "search.fs_uuid 33333333-3333-3333-3333-333333333333" windows
probar "reserva ajena intacta" 0 arctiva '[[ "$(reserva)" == windows ]]'
preparar "search.fs_uuid 33333333-3333-3333-3333-333333333333" "search.fs_uuid 33333333-3333-3333-3333-333333333333"
probar "reserva propia renovada" 0 arctiva '[[ "$(reserva)" == grub-nuevo* ]]'
preparar; FAKE_FAIL=1
probar "fallo: copia, reparación, limpieza y reintento" 0 arctiva \
    '[[ -n "$(find "${r}/var/lib/arctiva-installer" -name "esp-*.img")" && ! -e "${esp}/EFI/arctiva/parcial" ]] && grep -q "^umount" "${tmp}/log" && grep -q "fsck.vfat -a /dev/esp" "${tmp}/log" && grep -q "fsck.vfat -n /dev/esp" "${tmp}/log" && grep -q "^mount -o umask=0077 -- /dev/esp" "${tmp}/log"'
preparar "search.fs_uuid 33333333-3333-3333-3333-333333333333"; FAKE_FAIL=1
probar "fallo con carpeta previa: no se borra y se usa arctiva-2" 0 arctiva-2 '[[ -e "${esp}/EFI/arctiva/parcial" ]]'
preparar; FAKE_FAIL=1 FAKE_FSCK_A=1
probar "fsck -a corrige errores (código 1): sigue" 0 arctiva
preparar; FAKE_FAIL=1 FAKE_FSCK_N=1
probar "la ESP sigue con errores: sale con 1" 1 - 'grep -q "no se ha podido reparar" "${tmp}/out" && grep -q "could not be repaired" "${tmp}/out"'
preparar; FAKE_FAIL=2
probar "doble fallo: sale con 1 y mensaje en los dos idiomas" 1 - \
    'grep -q "^ERROR: grub-install ha fallado otra vez" "${tmp}/out" && grep -q "^ERROR: grub-install failed again" "${tmp}/out" && ! grep -q grub-mkconfig "${tmp}/log"'
preparar; rm -rf "${tmp}/sys/firmware/efi"
probar "sin UEFI: sale con 1 sin tocar nada" 1 - '[[ ! -s "${tmp}/log" ]]'

if (( fallos )); then echo "${fallos} casos fallidos" >&2; exit 1; fi
echo "Todo correcto."
