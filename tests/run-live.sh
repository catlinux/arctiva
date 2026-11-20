#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Arranca la ISO (o el sistema ya instalado) en QEMU/KVM con UEFI y la muestra
# en el navegador con noVNC. Pensado para un equipo Linux al que se entra por SSH.
set -euo pipefail

usage() {
    cat <<EOF
Uso: tests/run-live.sh [-d] [-r] [archivo.iso]

  (sin opciones)  Arranca la ISO más reciente de out/ con el disco virtual conectado.
  -d              Arranca solo desde el disco virtual (sistema ya instalado).
  -r              Borra el disco virtual y la NVRAM UEFI y empieza de cero.

Visor: http://localhost:6080/vnc.html (VS Code Remote-SSH reenvía el puerto;
si no, «ssh -L 6080:localhost:6080 <equipo>»). Ctrl+C cierra la VM.

Variables: VM_DIR (~/arctiva-vm), MEM (4096), CPUS (2), DISK_SIZE (40G),
VNC_DISPLAY (10, puerto 5910), OVMF_CODE, OVMF_VARS, NOVNC_WEB (/usr/share/novnc).
EOF
}

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
vm_dir="${VM_DIR:-$HOME/arctiva-vm}"
mem="${MEM:-4096}"
cpus="${CPUS:-2}"
disk_size="${DISK_SIZE:-40G}"
ovmf_code="${OVMF_CODE:-/usr/share/OVMF/OVMF_CODE_4M.fd}"
ovmf_vars="${OVMF_VARS:-/usr/share/OVMF/OVMF_VARS_4M.fd}"
novnc_web="${NOVNC_WEB:-/usr/share/novnc}"
# :1 (5901) suele estar ocupado por un escritorio VNC del propio equipo.
vnc_display="${VNC_DISPLAY:-10}"
vnc_port=$((5900 + vnc_display))

die() { echo "run-live.sh: $*" >&2; exit 1; }

boot_disk=0
reset=0
while getopts 'drh' opt; do
    case "$opt" in
        d) boot_disk=1 ;;
        r) reset=1 ;;
        h) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done
shift $((OPTIND - 1))

command -v qemu-system-x86_64 >/dev/null || die "falta QEMU (paquete qemu-system-x86)."
command -v websockify >/dev/null || die "falta noVNC (sudo apt install novnc)."
[[ -f "$ovmf_code" && -f "$ovmf_vars" ]] || die "no se encuentra OVMF (paquete ovmf; variables OVMF_CODE/OVMF_VARS)."
[[ -w /dev/kvm ]] || die "sin acceso a /dev/kvm (añade tu usuario al grupo kvm)."

mkdir -p -- "$vm_dir"
disk="${vm_dir}/disco.qcow2"
nvram="${vm_dir}/OVMF_VARS.fd"
if (( reset )); then
    rm -f -- "$disk" "$nvram"
fi
[[ -f "$disk" ]] || qemu-img create -q -f qcow2 "$disk" "$disk_size"
[[ -f "$nvram" ]] || cp -- "$ovmf_vars" "$nvram"

cdrom=()
if (( ! boot_disk )); then
    iso="${1:-$(ls -t "${repo_dir}"/out/arctiva-*.iso 2>/dev/null | head -n1 || true)}"
    [[ -n "$iso" && -f "$iso" ]] || die "no hay ISO: constrúyela o pásala como argumento."
    cdrom=(-drive "file=${iso},media=cdrom,readonly=on")
    echo "ISO: ${iso}"
fi

cleanup() { kill "${qemu_pid:-}" "${ws_pid:-}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp "$cpus" -m "$mem" \
    -drive "if=pflash,format=raw,readonly=on,file=${ovmf_code}" \
    -drive "if=pflash,format=raw,file=${nvram}" \
    -drive "file=${disk},if=virtio,format=qcow2" \
    "${cdrom[@]}" \
    -device virtio-vga -device qemu-xhci -device usb-tablet \
    -nic user,model=virtio-net-pci \
    -vnc "127.0.0.1:${vnc_display}" &
qemu_pid=$!
sleep 2
kill -0 "$qemu_pid" 2>/dev/null || die "QEMU no ha arrancado (¿puerto ${vnc_port} ocupado? prueba VNC_DISPLAY=11)."

websockify --web="$novnc_web" 127.0.0.1:6080 "127.0.0.1:${vnc_port}" >"${vm_dir}/websockify.log" 2>&1 &
ws_pid=$!

echo "Disco virtual: ${disk}"
echo "Abre http://localhost:6080/vnc.html y pulsa «Connect». Ctrl+C cierra la VM."
wait "$qemu_pid"
