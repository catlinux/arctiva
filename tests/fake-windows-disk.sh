#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Simula un disco con Windows para probar la página «Comprobación» del instalador sin instalar
# Windows. Se ejecuta como root dentro de la sesión live, sobre un disco virtual de pruebas.
# BORRA EL DISCO INDICADO.
#
#   limpio     ESP con EFI/Microsoft/Boot/bootmgfw.efi, NTFS (NTFS_SIZE, 8G por defecto) y 1 GiB
#              sin formato
#   hibernado  marca el NTFS como hibernado (hiberfil.sys con cabecera HIBR)
#   bitlocker  quita la hibernación y pone la firma de BitLocker en la tercera partición
#
# Uso: sudo tests/fake-windows-disk.sh <limpio|hibernado|bitlocker> [/dev/vda]
# Necesita ntfsprogs (mkntfs). Después: /usr/lib/arctiva-installer/detect-system.
set -euo pipefail

modo="${1:?uso: $0 <limpio|hibernado|bitlocker> [disco]}"
disco="${2:-/dev/vda}"
ntfs_size="${NTFS_SIZE:-8G}"
[[ $EUID -eq 0 ]] || { echo "fake-windows-disk.sh: hay que ejecutarlo como root." >&2; exit 1; }
[[ -b "$disco" ]] || { echo "fake-windows-disk.sh: ${disco} no es un disco." >&2; exit 1; }

part() { lsblk -prno NAME "$disco" | sed -n "$(( $1 + 1 ))p"; }

# ntfs-3g (FUSE) tarda un momento en soltar el punto de montaje.
desmontar() {
    local _
    for _ in 1 2 3 4 5; do
        umount "$1" 2>/dev/null && { rmdir "$1"; return 0; }
        sleep 1
    done
    umount "$1"
}

case "$modo" in
    limpio)
        wipefs -af "$disco" >/dev/null
        sgdisk -Z "$disco" >/dev/null
        sgdisk -n1:0:+100M -t1:ef00 -n2:0:+"${ntfs_size}" -t2:0700 -n3:0:+1G -t3:0700 "$disco" >/dev/null
        partprobe "$disco"; udevadm settle
        mkfs.vfat -F32 "$(part 1)" >/dev/null
        mkntfs -Q -L Windows "$(part 2)" >/dev/null
        # Las particiones nuevas pueden conservar firmas de una ejecución anterior.
        dd if=/dev/zero of="$(part 3)" bs=1M count=1 conv=notrunc status=none
        mnt="$(mktemp -d)"
        mount -t vfat "$(part 1)" "$mnt"
        mkdir -p "${mnt}/EFI/Microsoft/Boot"
        echo "simulado" >"${mnt}/EFI/Microsoft/Boot/bootmgfw.efi"
        umount "$mnt"; rmdir "$mnt"
        ;;
    hibernado)
        mnt="$(mktemp -d)"
        ntfs-3g "$(part 2)" "$mnt"
        { printf 'HIBR'; head -c 8188 /dev/zero; } >"${mnt}/hiberfil.sys"
        desmontar "$mnt"
        ;;
    bitlocker)
        mnt="$(mktemp -d)"
        ntfs-3g -o remove_hiberfile "$(part 2)" "$mnt"
        desmontar "$mnt"
        # Firma de BitLocker de Vista: libblkid la reconoce sin más comprobaciones.
        dd if=/dev/zero of="$(part 3)" bs=1M count=1 conv=notrunc status=none
        printf '\xeb\x52\x90%s' '-FVE-FS-' | dd of="$(part 3)" bs=1 conv=notrunc status=none
        ;;
    *)
        echo "fake-windows-disk.sh: modo desconocido: ${modo}" >&2; exit 2 ;;
esac

udevadm settle
lsblk -fp "$disco"
