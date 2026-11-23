#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Prueba de instalación: arranca la ISO en QEMU (UEFI), recorre el instalador por VNC con
# coordenadas fijas (pantalla de 1280x800), reinicia desde el disco y comprueba que el sistema
# instalado llega a la pantalla de inicio de sesión. Detecta fallos como el del 0.4.1 (kernel con
# hueco que GRUB no podía leer), que solo se ven instalando y arrancando.
#
# Uso: tests/install-test.sh <archivo.iso> [--encrypt] [directorio-de-capturas]
# Necesita: qemu-system-x86_64 con KVM, OVMF, 7z, socat, python3 con venv y acceso a internet
# (instala vncdotool y pillow en un entorno temporal). Las contraseñas son de prueba.
# Variables opcionales: KEEP_DISK=<archivo> conserva el disco instalado; QEMU_NET=none prueba sin red.
set -euo pipefail

iso="${1:?Uso: tests/install-test.sh <archivo.iso> [--encrypt] [capturas]}"
shift
encrypt=0
out="install-test-out"
for a in "$@"; do
    case "$a" in
        --encrypt) encrypt=1 ;;
        *) out="$a" ;;
    esac
done
ovmf_code="${OVMF_CODE:-/usr/share/OVMF/OVMF_CODE_4M.fd}"
ovmf_vars="${OVMF_VARS:-/usr/share/OVMF/OVMF_VARS_4M.fd}"
display="${VNC_DISPLAY:-11}"
pass=arctivatest

[[ -f "$iso" ]] || { echo "install-test: no existe $iso" >&2; exit 2; }
[[ -w /dev/kvm ]] || { echo "install-test: hace falta KVM (/dev/kvm)." >&2; exit 2; }
mkdir -p -- "$out"

tmp="$(mktemp -d)"
qpid=""
cleanup() {
    [[ -z "$qpid" ]] || kill "$qpid" 2>/dev/null || true
    # KEEP_DISK=<archivo>: conserva el disco instalado para inspeccionarlo (qemu-nbd, mount).
    [[ -z "${KEEP_DISK:-}" || ! -f "$tmp/disco.qcow2" ]] || cp -- "$tmp/disco.qcow2" "$KEEP_DISK"
    rm -rf -- "$tmp"
}
trap cleanup EXIT

python3 -m venv "$tmp/venv" >/dev/null
"$tmp/venv/bin/pip" install -q vncdotool pillow >/dev/null
V=("$tmp/venv/bin/vncdo" --delay 150 -s "127.0.0.1::$((5900 + display))")
vnc() { "${V[@]}" "$@"; }
shot() { vnc capture "$out/$1.png"; }
# Fracaso con captura: el motivo queda en la imagen.
fail() { echo "FALLO: $*" >&2; shot fallo 2>/dev/null || true; exit 1; }

qemu_disk=("-drive" "file=$tmp/disco.qcow2,if=none,id=hd,format=qcow2" "-device" "virtio-blk-pci,drive=hd,bootindex=1")
start_qemu() {
    qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 2 -m 4096 \
        -drive "if=pflash,format=raw,readonly=on,file=$ovmf_code" \
        -drive "if=pflash,format=raw,file=$tmp/vars.fd" \
        "${qemu_disk[@]}" "$@" \
        -device virtio-vga -device qemu-xhci -device usb-tablet -nic "${QEMU_NET:-user,model=virtio-net-pci}" \
        -vnc "127.0.0.1:$display" -display none &
    qpid=$!
}
stop_qemu() { kill "$qpid" 2>/dev/null || true; wait "$qpid" 2>/dev/null || true; qpid=""; }

# Imagen no casi uniforme (no pantalla en negro) y pixel (x,y) con el color pedido ±tolerancia.
pixel_is() { # captura x y r g b tol
    "$tmp/venv/bin/python" - "$@" <<'PY'
import sys
from PIL import Image
f, x, y, r, g, b, tol = sys.argv[1], *map(int, sys.argv[2:])
p = Image.open(f).convert("RGB").getpixel((x, y))
sys.exit(0 if all(abs(a - c) <= tol for a, c in zip(p, (r, g, b))) else 1)
PY
}
not_black() {
    "$tmp/venv/bin/python" - "$1" <<'PY'
import sys
from PIL import Image, ImageStat
im = Image.open(sys.argv[1]).convert("L")
st = ImageStat.Stat(im)
sys.exit(0 if st.mean[0] > 25 and st.stddev[0] > 15 else 1)
PY
}

qemu-img create -f qcow2 "$tmp/disco.qcow2" 40G >/dev/null
cp -- "$ovmf_vars" "$tmp/vars.fd"

echo "== Arrancando la ISO"
start_qemu -drive "file=$iso,if=none,id=cd,media=cdrom,readonly=on" -device "ide-cd,drive=cd,bootindex=0"
sleep 8
vnc key enter   # entrada por defecto del menú de arranque
for _ in $(seq 1 40); do
    sleep 10
    shot live
    # Escritorio con la barra clara abajo (el instalador aún no se ha abierto)
    if pixel_is "$out/live.png" 300 780 234 238 250 25 2>/dev/null && not_black "$out/live.png"; then break; fi
done
pixel_is "$out/live.png" 300 780 234 238 250 25 || fail "la live no llegó al escritorio"

echo "== Abriendo el instalador"
vnc move 640 400 click 1 key alt-space pause 2 type "Install Arctiva" pause 3 key enter
sleep 25

echo "== Recorriendo el instalador (cifrado=$encrypt)"
next() { vnc move 1126 711 click 1 pause "${1:-4}"; }
next 4; next 4; next 4            # bienvenida, zona, teclado
vnc move 400 75 click 1 pause 2   # perfil Básico
next 5; next 9                    # perfiles, comprobación
vnc move 296 122 click 1 pause 4  # borrar disco
if (( encrypt )); then
    vnc move 296 492 click 1 pause 3
    vnc move 540 492 click 1 key ctrl-a key bsp type "$pass" move 786 492 click 1 key ctrl-a key bsp type "$pass" pause 2
fi
next 6                            # usuarios
vnc move 735 193 click 1 key ctrl-a type prueba \
    move 526 260 click 1 key ctrl-a type prueba \
    move 943 260 click 1 key ctrl-a type arctivapc \
    move 526 365 click 1 type "$pass" move 943 365 click 1 type "$pass" pause 2
next 6                            # resumen
shot resumen
vnc move 1120 711 click 1 pause 4 # Instalar
vnc move 700 425 click 1 pause 3  # confirmar

echo "== Instalando (puede tardar de 10 a 25 minutos)"
done_ok=0
for _ in $(seq 1 180); do
    sleep 10
    vnc move $((600 + RANDOM % 80)) 400 2>/dev/null || true
    shot progreso
    # Página final: botón «Hecho» azul abajo a la derecha (dos puntos del botón, lejos de su texto)
    if pixel_is "$out/progreso.png" 1100 700 29 78 216 25 2>/dev/null && pixel_is "$out/progreso.png" 1150 700 29 78 216 25 2>/dev/null; then done_ok=1; break; fi
done
(( done_ok )) || fail "el instalador no llegó a la pantalla final"
shot instalado

echo "== Reiniciando desde el disco"
stop_qemu
qemu_disk=("-drive" "file=$tmp/disco.qcow2,if=none,id=hd,format=qcow2" "-device" "virtio-blk-pci,drive=hd,bootindex=1")
start_qemu
if (( encrypt )); then
    sleep 18
    vnc type "$pass" key enter
fi
ok=0
for _ in $(seq 1 30); do
    sleep 10
    shot arranque
    # Pantalla de inicio de sesión (fondo azul oscuro con el reloj claro) o escritorio
    if not_black "$out/arranque.png" && ! pixel_is "$out/arranque.png" 5 5 0 0 0 5; then ok=1; break; fi
done
(( ok )) || fail "el sistema instalado no llegó al inicio de sesión"
sleep 30
shot login
echo "== Iniciando sesión"
vnc move 600 481 click 1 type "$pass" key enter
sleep 45
shot escritorio
not_black "$out/escritorio.png" || fail "no hay escritorio tras iniciar sesión"
echo "Correcto: instalación y arranque desde el disco (cifrado=$encrypt). Capturas en $out/."
