#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Prueba install-drivers en modo --upgrade (Arctiva Center) con pacman, systemctl y mkinitcpio
# falsos y salidas reales de lspci (tests/fixtures). No necesita root ni red.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
files="${here}/../packages/arctiva-hardware/files"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

mkdir -p "${tmp}/bin" "${tmp}/raiz"
ln -s "${files}/usr/bin/arctiva-gpu" "${tmp}/bin/arctiva-gpu"
for cmd in pacman systemctl mkinitcpio; do
    cat >"${tmp}/bin/${cmd}" <<'FAKE'
#!/usr/bin/env bash
# «pacman -r DIR -Q pkg» (arctiva-gpu): nada instalado. El resto se anota y sale con $FAKE_RC.
[[ "$(basename "$0")" == pacman && "${1:-}" == -r ]] && exit 1
echo "$(basename "$0") $*" >>"$FAKE_LOG"
exit "${FAKE_RC:-0}"
FAKE
    chmod +x "${tmp}/bin/${cmd}"
done
export PATH="${tmp}/bin:${PATH}"

fallos=0
# probar <fixture> <rc de pacman> <código esperado> <llamadas esperadas, separadas por «|»>
probar() {
    local fixture="$1" rc="$2" esperado="$3" llamadas="$4" real obtenido
    : >"${tmp}/log"
    rm -rf "${tmp}/raiz/etc"
    set +e
    FAKE_LOG="${tmp}/log" FAKE_RC="$rc" ARCTIVA_LSPCI_FILE="${here}/fixtures/lspci-${fixture}.txt" \
        "${files}/usr/lib/arctiva/install-drivers" --upgrade "${tmp}/raiz" >"${tmp}/salida" 2>&1
    real=$?
    set -e
    obtenido="$(paste -sd'|' "${tmp}/log")"
    if [[ "$real" == "$esperado" && "$obtenido" == "$llamadas" ]]; then
        echo "ok    ${fixture} rc=${rc} → ${real}"
    else
        echo "FALLO ${fixture} rc=${rc}: código ${real} (esperado ${esperado}); llamadas «${obtenido}» (esperadas «${llamadas}»)"
        fallos=$((fallos + 1))
    fi
}

# La raíz no es «/»: las órdenes van por chroot, que aquí se simula ejecutando la orden tal cual.
cat >"${tmp}/bin/chroot" <<'FAKE'
#!/usr/bin/env bash
shift
exec "$@"
FAKE
chmod +x "${tmp}/bin/chroot"

probar rtx4060 0 0 "pacman -Syu --needed --noconfirm -- nvidia-open nvidia-utils|mkinitcpio -P"
[[ -f "${tmp}/raiz/etc/mkinitcpio.conf.d/arctiva-nvidia.conf" ]] || { echo "FALLO falta arctiva-nvidia.conf"; fallos=$((fallos + 1)); }
probar rtx4060 1 1 "pacman -Syu --needed --noconfirm -- nvidia-open nvidia-utils"
[[ ! -e "${tmp}/raiz/etc/mkinitcpio.conf.d/arctiva-nvidia.conf" ]] || { echo "FALLO arctiva-nvidia.conf sin controlador"; fallos=$((fallos + 1)); }
probar portatil-hibrido 0 0 "pacman -Syu --needed --noconfirm -- nvidia-open nvidia-utils switcheroo-control|systemctl enable --now switcheroo-control|mkinitcpio -P"
probar amd 0 0 ""
probar gtx1060 0 0 ""
probar qemu 0 0 ""

if (( fallos )); then
    echo "${fallos} comprobaciones fallidas" >&2
    exit 1
fi
echo "Todo correcto."
