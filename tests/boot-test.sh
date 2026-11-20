#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Arranca la ISO en QEMU con firmware UEFI (OVMF), sin pantalla, y espera a que
# el usuario «live» tenga sesión gráfica (D-15). El kernel se arranca directamente
# para poder añadir la consola serie; el menú de systemd-boot se prueba a mano.
set -euo pipefail

iso="${1:?Uso: sudo tests/boot-test.sh <archivo.iso> [registro]}"
log="${2:-boot-test.log}"
ovmf="${OVMF:-/usr/share/ovmf/OVMF.fd}"

[[ $EUID -eq 0 ]] || { echo "boot-test.sh: hay que ejecutarlo como root." >&2; exit 1; }
[[ -f "$ovmf" ]] || { echo "boot-test.sh: no se encuentra OVMF en ${ovmf} (variable OVMF)." >&2; exit 1; }

if [[ -w /dev/kvm ]]; then
    accel=(-enable-kvm -cpu host)
    timeout_s="${BOOT_TIMEOUT:-600}"
else
    echo "Sin KVM: emulación por software, mucho más lenta."
    accel=(-cpu max)
    timeout_s="${BOOT_TIMEOUT:-2400}"
fi

tmp="$(mktemp -d)"
cleanup() {
    [[ -z "${qemu_pid:-}" ]] || kill "$qemu_pid" 2>/dev/null || true
    if mountpoint -q "${tmp}/iso"; then umount "${tmp}/iso"; fi
    rm -rf -- "$tmp"
}
trap cleanup EXIT

mkdir "${tmp}/iso"
mount -o loop,ro -- "$iso" "${tmp}/iso"
cp -- "${tmp}/iso/arctiva/boot/x86_64/vmlinuz-linux" "${tmp}/iso/arctiva/boot/x86_64/initramfs-linux.img" "$tmp/"
umount "${tmp}/iso"
uuid="$(blkid -s UUID -o value -- "$iso")"

: >"$log"
qemu-system-x86_64 "${accel[@]}" -m 4096 -smp 2 \
    -bios "$ovmf" \
    -drive "file=${iso},media=cdrom,readonly=on" \
    -kernel "${tmp}/vmlinuz-linux" -initrd "${tmp}/initramfs-linux.img" \
    -append "archisobasedir=arctiva archisosearchuuid=${uuid} systemd.unit=graphical.target systemd.firstboot=off console=ttyS0,115200" \
    -display none -serial "file:${log}" -no-reboot &
qemu_pid=$!

success='Session [0-9]+ of User live'
for ((elapsed = 0; elapsed < timeout_s; elapsed += 5)); do
    if grep -Eq "$success" "$log"; then
        echo "Correcto: sesión gráfica del usuario live en ${elapsed} s."
        grep -E 'Failed to start|FAILED' "$log" || true
        exit 0
    fi
    kill -0 "$qemu_pid" 2>/dev/null || break
    sleep 5
done

echo "Error: no se llegó a la sesión del usuario live en ${timeout_s} s. Final del registro:" >&2
tail -n 60 "$log" >&2
exit 1
