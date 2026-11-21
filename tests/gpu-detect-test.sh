#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Prueba arctiva-gpu con salidas reales de lspci -nn (tests/fixtures/lspci-*.txt).
# No necesita root ni hardware: con --root se simula pacman con un archivo de paquetes.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
gpu="${here}/../packages/arctiva-hardware/files/usr/bin/arctiva-gpu"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

# pacman falso: «pacman -r DIR -Q -- paquete» sale 0 si paquete figura en DIR/paquetes.
mkdir -p "${tmp}/bin" "${tmp}/destino"
cat >"${tmp}/bin/pacman" <<'FAKE'
#!/usr/bin/env bash
dir="$2"; pkg="${@: -1}"
grep -qx -- "$pkg" "${dir}/paquetes"
FAKE
chmod +x "${tmp}/bin/pacman"
export PATH="${tmp}/bin:${PATH}"

fallos=0
# comprobar <fixture> <clave> <valor esperado> [args de arctiva-gpu]
comprobar() {
    local fixture="$1" clave="$2" esperado="$3"; shift 3
    local real
    real="$(ARCTIVA_LSPCI_FILE="${here}/fixtures/lspci-${fixture}.txt" "$gpu" "$@" | sed -n "s/^${clave}=//p")"
    if [[ "$real" == "$esperado" ]]; then
        echo "ok    ${fixture} ${clave}=${real}"
    else
        echo "FALLO ${fixture} ${clave}: esperado «${esperado}», obtenido «${real}»"
        fallos=$((fallos + 1))
    fi
}

: >"${tmp}/destino/paquetes"
comprobar rtx4060 gpus nvidia
comprobar rtx4060 packages "nvidia-open nvidia-utils"
comprobar rtx4060 nvidia_kms 1
comprobar rtx4060 warning ""
comprobar gtx1060 gpus nvidia-legacy
comprobar gtx1060 packages ""
comprobar gtx1060 nvidia_kms 0
comprobar gtx1060 warning nvidia-legacy
comprobar portatil-hibrido gpus "intel nvidia"
comprobar portatil-hibrido packages "nvidia-open nvidia-utils switcheroo-control"
comprobar portatil-hibrido services switcheroo-control
comprobar amd gpus amd
comprobar amd packages ""
comprobar amd nvidia_kms 0
comprobar qemu gpus virtual
comprobar qemu packages ""
comprobar qemu services ""

printf '%s\n' linux-lts steam >"${tmp}/destino/paquetes"
comprobar rtx4060 packages "nvidia-open nvidia-utils nvidia-open-lts lib32-nvidia-utils" --root "${tmp}/destino"
comprobar gtx1060 packages "" --root "${tmp}/destino"

if (( fallos )); then
    echo "${fallos} comprobaciones fallidas" >&2
    exit 1
fi
echo "Todo correcto."
